#!/usr/bin/env python3
import os, re, json, time, platform
from collections import OrderedDict
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

def get_config_path():
    """Return the platform-appropriate path for the config file."""
    system = platform.system()

    if system == "Windows":
        base_dir = Path.home() / "AppData" / "Local"
    elif system in ("Linux", "Darwin"):
        base_dir = Path.home() / ".config"
    else:
        base_dir = Path(__file__).parent

        base_dir.mkdir(parents=True, exist_ok=True)

    return base_dir / "pysongbooker.json"

CONFIG_FILE = get_config_path()

def load_config():
    """Load saved directories from config.json if available."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to read config file: {e}")
    return {}

def save_config(config):
    """Save directories to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"[INFO] Saved configuration to {CONFIG_FILE}")
    except Exception as e:
        print(f"[WARN] Could not save config file: {e}")

def autodetect_lotro_music():
    """Try to auto-detect the LOTRO music directory under Steam."""
    home = os.path.expanduser("~")
    system = platform.system().lower()

    possible_paths = []

    if "windows" in system:
        possible_paths.append(os.path.join(home, "Documents", "The Lord of the Rings Online", "Music"))
    else:
        for root in [
            os.path.join(home, ".local", "share", "Steam", "steamapps", "compatdata"),
             os.path.join(home, ".wine", "drive_c", "users", os.getenv("USER", "user"), "Documents"),
        ]:
            for dirpath, dirnames, filenames in os.walk(root):
                if dirpath.endswith("The Lord of the Rings Online/Music"):
                    possible_paths.append(dirpath)

    return possible_paths[0] if possible_paths else None

def autodetect_lotro_plugin_dirs():
    """Detect all LOTRO PluginData/<account>/AllServers directories."""
    candidates = []
    possible_paths = [
        Path.home() / ".local/share/Steam/steamapps/compatdata",
    ]

    system = platform.system().lower()
    if "windows" in system:
        possible_paths.append(Path.home() / "Documents" / "The Lord of the Rings Online" / "PluginData")

    plugin_roots = []
    for base in possible_paths:
        if not base.exists():
            continue

        if "compatdata" in str(base):
            for entry in base.iterdir():
                docs = entry / "pfx/drive_c/users/steamuser/Documents/The Lord of the Rings Online/PluginData"
                if docs.exists():
                    plugin_roots.append(docs)
        else:
            plugin_roots.append(base)

    # scan for account directories under each base
    for root in plugin_roots:
        for account_dir in root.iterdir():
            if not account_dir.is_dir():
                continue
            allservers = account_dir / "AllServers"
            if not allservers.exists():
                try:
                    allservers.mkdir(parents=True, exist_ok=True)
                    print(f"[INFO] Created missing directory: {allservers}")
                except Exception as e:
                    print(f"[WARN] Could not create AllServers directory at {allservers}")
                    continue

            candidates.append(str(allservers))

    if candidates:
        print(f"[INFO] Found {len(candidates)} LOTRO PluginData directories:")
        for c in candidates:
            print(f"   → {c}")
    else:
        print("[WARN] No LOTRO PluginData directories found automatically.")

    return candidates

def lua_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')

def choose_directories():
    """Prompt user to select scan and output directories via file dialog."""
    root = tk.Tk()
    root.withdraw()  # Hide the empty main window
    root.update()

    config = load_config()

    if not config.get("scan_dir"):
        autodetected = autodetect_lotro_music()
        if autodetected:
            config["scan_dir"] = autodetected
            save_config(config)

    if not config.get("plugins_dir"):
        autodetected_plugins = autodetect_lotro_plugin_dirs()
        if autodetected_plugins:
            config["plugins_dir"] = autodetected_plugins[0]
            save_config(config)

    last_scan = config.get("scan_dir", ".")
    last_plugins = config.get("plugins_dir", ".")

    print(f"[INFO] Last scan dir: {last_scan}")
    print(f"[INFO] Last plugins dir: {last_plugins}")

    print("[INFO] Please select your LOTRO Music directory...")
    scan_dir = filedialog.askdirectory(title="Select LotRO Music Directory", initialdir=last_scan)

    if not scan_dir:
        print("[WARN] User cancelled directory selection.")
        sys.exit(0)

    print(f"[INFO] Selecting plugins output directory, found: {last_plugins}")
    plugins_dir = filedialog.askdirectory(title="Select LotRO PluginData Output Directory", initialdir=last_plugins)

    if not plugins_dir:
        print("[WARN] User cancelled directory selection.")
        sys.exit(0)

    config["scan_dir"] = scan_dir
    config["plugins_dir"] = plugins_dir
    save_config(config)

    return scan_dir, plugins_dir

def parse_abc_headers(path):
    """Parse common ABC headers (T:, P:, V:, I:, C:, Z:)"""
    title = None
    parts = []
    composer = None
    transcriber = None
    instrument = None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('%'):
                    continue
                if line.startswith("T:") and title is None:
                    title = line[2:].strip()
                elif line.startswith("P:"):
                    p = line[2:].strip()
                    if p and p not in parts:
                        parts.append(p)
                elif line.startswith("V:"):
                    v = line[2:].strip()
                    if v and v not in parts:
                        parts.append(v)
                elif line.startswith("I:") and instrument is None:
                    instrument = line[2:].strip()
                    if instrument and instrument not in parts:
                        parts.append(instrument)
                elif line.startswith("C:") and composer is None:
                    composer = line[2:].strip()
                elif line.startswith("Z:") and transcriber is None:
                    transcriber = line[2:].strip()
                # lightweight: stop early if we have title and at least one other header
                if title and (parts or composer or transcriber):
                    # keep scanning a little (some files put metadata later), but this keeps it quick
                    pass
    except Exception as e:
        print(f"[WARN] Unable to read {path}: {e}")

    if not title:
        title = os.path.splitext(os.path.basename(path))[0]
    return {
        "title": title,
        "parts": parts,
        "composer": composer,
        "transcriber": transcriber,
        "instrument": instrument
    }

def build_songs(scan_dir):
    """Scan scan_dir and build an OrderedDict of songs grouped by Title."""
    abc_files = []
    for root, _, files in os.walk(scan_dir):
        for fn in files:
            if fn.lower().endswith(".abc"):
                abc_files.append(os.path.join(root, fn))
    print(f"[INFO] Found {len(abc_files)} .abc files under {scan_dir}")

    songs_by_title = OrderedDict()
    song_index = 1

    for path in sorted(abc_files):
        meta = parse_abc_headers(path)
        dirname = os.path.dirname(path)
        rel_dir = os.path.relpath(dirname, scan_dir)
        if rel_dir in ("", "."):
            filepath = "/"
        else:
            filepath = "/" + rel_dir.replace(os.sep, "/").strip("/") + "/"

        filename_base = os.path.splitext(os.path.basename(path))[0]
        title = meta.get("title", filename_base)
        transcriber = meta.get("transcriber", "")
        composer = meta.get("composer", "")

        abc_id = "0"
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("X:"):
                        abc_id = line[2:].strip()
                        break
        except Exception as e:
            print(f"[WARN] Could not read X: from {path}: {e}")

        track = {
            "Id": abc_id,
            "Name": title
        }

        songs_by_title[song_index] = {
            "Filepath": filepath,
            "Filename": filename_base,
            "Tracks": [track],
            "Transcriber": transcriber,
            "Artist": composer
        }
        #print(f"[DEBUG] Added song {song_index}: {filename_base} (Id={abc_id}, Title={title})")
        song_index += 1

    print(f"[INFO] Processed {len(songs_by_title)} individual song files.")
    return songs_by_title

def render_lua(songs):
    """Render the OrderedDict into the Songbook .plugindata Lua structure."""
    out = []
    out.append("return")
    out.append("{")
    out.append('\t["Directories"] =')
    out.append('\t{')
    out.append('\t\t[1] = "/",')
    out.append('\t},')
    out.append('\t["Songs"] =')
    out.append('\t{')
    idx = 1
    for title, info in songs.items():
        out.append(f'\t\t[{idx}] =')
        out.append('\t\t{')
        out.append(f'\t\t\t["Filepath"] = "{lua_escape(info["Filepath"])}",')
        out.append(f'\t\t\t["Filename"] = "{lua_escape(info["Filename"])}",')
        out.append('\t\t\t["Tracks"] =')
        out.append('\t\t\t{')
        for t_i, t in enumerate(info["Tracks"], start=1):
            out.append(f'\t\t\t\t[{t_i}] =')
            out.append('\t\t\t\t{')
            out.append(f'\t\t\t\t\t["Id"] = "{lua_escape(t["Id"])}",')
            out.append(f'\t\t\t\t\t["Name"] = "{lua_escape(t["Name"])}"')
            out.append('\t\t\t\t},')
        out.append('\t\t\t},')
        if info.get("Transcriber"):
            out.append(f'\t\t\t["Transcriber"] = "{lua_escape(info["Transcriber"])}",')
        if info.get("Artist"):
            out.append(f'\t\t\t["Artist"] = "{lua_escape(info["Artist"])}",')
        out.append('\t\t},')
        idx += 1
    out.append('\t},')
    out.append("}")
    return "\n".join(out)

def main(scan_dir=".", output_path=None):
    start = time.time()
    scan_dir = os.path.abspath(scan_dir)
    output_path = os.path.join(output_path, "SongbookData.plugindata")
    
    print(f"[INFO] scan_dir = {scan_dir}")
    songs = build_songs(scan_dir)
    lua_text = render_lua(songs)

    print(f"[INFO] Wrote {output_path}")
    # ensure output dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(lua_text)
    elapsed = time.time() - start
    print(f"[INFO] Songs written: {len(songs)}")
    print(f"[INFO] Execution time: {elapsed:.2f} seconds")

def run():
    print("Updating Music database...")
    import sys
    sd, od = choose_directories()
    main(scan_dir=sd, output_path=od)

if __name__ == "__main__":
    run()
