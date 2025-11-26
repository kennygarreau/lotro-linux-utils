#!/usr/bin/env python3
import os
import sys
import json
import shutil
import zipfile
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

def get_config_path():
    """Return OS-specific config file path."""
    home = Path.home()
    if platform.system().lower() == "windows":
        config_dir = Path(os.getenv("APPDATA", home / "AppData/Roaming"))
    else:
        config_dir = home / ".config"
    #config_dir = config_dir / "pysongbooker"
    #config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "lotro_plugin_installer.json"


def load_config():
    path = get_config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not read config: {e}")
    return {}


def save_config(cfg):
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        print(f"[INFO] Saved config to {path}")
    except Exception as e:
        print(f"[WARN] Could not save config: {e}")


def autodetect_lotro_plugins():
    """Try to find LOTRO PluginData/<account>/AllServers or Plugins dirs."""
    candidates = []
    base_paths = [
        Path.home() / ".local/share/Steam/steamapps/compatdata",
    ]
    sysname = platform.system().lower()
    if "windows" in sysname:
        base_paths.append(Path.home() / "Documents" / "The Lord of the Rings Online" / "Plugins")

    for base in base_paths:
        if not base.exists():
            continue
        if "compatdata" in str(base):
            for entry in base.iterdir():
                docs = entry / "pfx/drive_c/users/steamuser/Documents/The Lord of the Rings Online/Plugins"
                if docs.exists():
                    candidates.append(str(docs))
                    # for acct in docs.iterdir():
                    #     plugins_dir = acct / "Plugins"
                    #     if plugins_dir.exists():
                    #         candidates.append(str(plugins_dir))
        else:
            for acct in base.iterdir():
                plugins_dir = acct / "Plugins"
                if plugins_dir.exists():
                    candidates.append(str(plugins_dir))

    if candidates:
        print(f"[INFO] Found {len(candidates)} LOTRO plugin directories.")
    else:
        print("[WARN] No plugin directories found.")
    return candidates


def select_from_list(options, title="Select LOTRO Plugin Directory"):
    """Show a GUI list selector when multiple plugin directories are found."""
    selection = {"value": None}

    def on_select():
        sel = listbox.curselection()
        if sel:
            selection["value"] = options[sel[0]]
            root.quit()
    def on_cancel():
        root.quit()

    root = tk.Tk()
    root.title(title)

    root.attributes("-topmost", True)
    root.geometry("700x400+200+200")

    tk.Label(root, text="Multiple LOTRO plugin directories found.\nPlease select the correct one:",
             font=("Segoe UI", 10)).pack(pady=10)

    listbox = tk.Listbox(root, width=100, height=10, selectmode=tk.SINGLE)
    for opt in options:
        listbox.insert(tk.END, opt)
    listbox.pack(pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Select", width=12, command=on_select).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cancel", width=12, command=on_cancel).pack(side=tk.LEFT, padx=5)

    root.lift()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    root.mainloop()

    root.destroy()

    if not selection["value"]:
        print("[WARN] No directory selected.")
        sys.exit(0)

    return selection["value"]


def choose_zip_and_install():
    cfg = load_config()

    home = Path.home()
    downloads_dir = home / "Downloads"
    if "downloads_dir" in cfg and Path(cfg["downloads_dir"]).exists():
        downloads_dir = Path(cfg["downloads_dir"])

    root = tk.Tk()
    root.withdraw()
    zip_path = filedialog.askopenfilename(
        title="Select a LOTRO Plugin .zip file",
        initialdir=downloads_dir,
        filetypes=[("ZIP files", "*.zip")],
    )
    if not zip_path:
        print("[WARN] User cancelled.")
        sys.exit(0)

    cfg["downloads_dir"] = str(Path(zip_path).parent)
    save_config(cfg)

    autodetected = autodetect_lotro_plugins()
    target_dir = None
    if autodetected:
        if len(autodetected) == 1:
            target_dir = autodetected[0]
        else:
            target_dir = select_from_list(autodetected)
    else:
        messagebox.showinfo("LOTRO Plugin Directory", "Please select your LOTRO Plugins directory manually.")
        target_dir = filedialog.askdirectory(title="Select LOTRO Plugins Directory")

    if not target_dir:
        print("[WARN] No output directory selected.")
        sys.exit(0)

    cfg["lotro_plugin_dir"] = target_dir
    save_config(cfg)

    print("[DEBUG] creating temp unzip dir")
    temp_dir = Path.home() / ".lotro_plugin_tmp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Extracting {zip_path} to {temp_dir}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    target = Path(target_dir)
    for item in temp_dir.iterdir():
        dest = target / item.name
        if dest.exists():
            print(f"[WARN] Overwriting existing: {dest}")
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
        print(f"[INFO] Installed: {dest}")

    shutil.rmtree(temp_dir)
    messagebox.showinfo("Success", f"Plugin installed successfully to:\n{target_dir}")

def run():
    print("Running plugin installer!")
    choose_zip_and_install()

if __name__ == "__main__":
    choose_zip_and_install()
