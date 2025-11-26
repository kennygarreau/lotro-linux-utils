#!/usr/bin/env python3
"""
LOTRO Multibox Launcher (Python + GE-Proton)
- Launches user-configurable number of LOTRO clients
- Isolated prefixes (per-client)
- Auto-fills username
- Places windows in 2×3 grid on a 4K display (not working)
"""

import os
import time
import subprocess
from pathlib import Path
import pyautogui
import keyring

HOME = Path.home()

# ---------------------- USER SETTINGS ----------------------

PROTON = HOME / ".local/share/Steam/compatibilitytools.d/GE-Proton10-15/proton"
BASE_COMPAT = HOME / ".local/share/Steam/steamapps/compatdata/4187400038/pfx"
LAUNCHER_EXE = (
    BASE_COMPAT
    / "drive_c/Program Files (x86)/StandingStoneGames/The Lord of the Rings Online/LotroLauncher.exe"
)

#USERFILE = HOME / "lotro-usernames.txt"
USERFILE = Path("lotro-usernames.sample")

CLIENT_PREFIX_ROOT = HOME / "lotro_prefixes"
CLIENT_DOCS_ROOT = HOME / "lotro_docs"
NUM_CLIENTS = 6
DELAY_BETWEEN_LAUNCHES = 10

USERNAME_DELAY = 0.02

# Grid size (4K, 2×3 layout)
TILE_W = 1920
TILE_H = 720

POSITIONS = [
    (0, 0),
    (1920, 0),
    (0, 720),
    (1920, 720),
    (0, 1440),
    (1920, 1440),
]


# ----------------------- HELPERS ---------------------------

def read_usernames():
    if not USERFILE.exists():
        print(f"Missing username file: {USERFILE}")
        sys.exit(1)

    lines = [l.strip() for l in USERFILE.read_text().splitlines() if l.strip()]
    if len(lines) < NUM_CLIENTS:
        print(f"You must supply {NUM_CLIENTS} usernames.")
        sys.exit(1)

    return lines[:NUM_CLIENTS]


def ensure_client_dirs():
    CLIENT_PREFIX_ROOT.mkdir(parents=True, exist_ok=True)
    CLIENT_DOCS_ROOT.mkdir(parents=True, exist_ok=True)

    prefixes = []
    docs = []

    for i in range(1, NUM_CLIENTS + 1):
        pfx = CLIENT_PREFIX_ROOT / f"prefix{i}"
        doc = CLIENT_DOCS_ROOT / f"client{i}"
        pfx.mkdir(parents=True, exist_ok=True)
        doc.mkdir(parents=True, exist_ok=True)
        prefixes.append(pfx)
        docs.append(doc)

    return prefixes, docs

def set_window_title(prefix: Path, title: str):
    """
    Write Wine-compatible registry entries to set window title.
    Proton respects this.
    """
    reg_file = prefix / "set_title.reg"
    reg_file.write_text(f'''
    REGEDIT4

    [HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktop]
    "Name"="{title}"
    ''')

    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix / "pfx")

    subprocess.run([
        str(PROTON),
        "run",
        "regedit",
        str(reg_file)
    ], env=env)

def load_credentials(usernames):
    service = "lotro-multibox"
    creds = []
    for user in usernames:
        pw = keyring.get_password(service, user)
        if not pw:
            raise ValueError(f"No password stored for {user}")
        creds.append((user, pw))
    return creds


def launch_client(prefix: Path, docs: Path, title: str):

    set_window_title(prefix, title)

    env = os.environ.copy()
    env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(HOME / ".local/share/Steam")
    env["STEAM_COMPAT_DATA_PATH"] = str(prefix)
    env["WINEPREFIX"] = str(prefix / "pfx")
    env["WINE_DOCUMENTS"] = str(docs)
    #subprocess.Popen([str(PROTON), "run", str(LAUNCHER_EXE)], env=env)
    cmd = [
        str(PROTON),
        "run",
        str(LAUNCHER_EXE)
    ]

    subprocess.Popen(cmd, env=env)

# -------------------------- MAIN ---------------------------

def run():
    usernames = read_usernames()
    credentials = load_credentials(usernames)
    prefixes, docs_dirs = ensure_client_dirs()

    print(f"Launching {NUM_CLIENTS} LOTRO clients under GE-Proton (Wayland)...")

    for i in range(NUM_CLIENTS):
        prefix = prefixes[i]
        docs = docs_dirs[i]
        title = f"Band Client {i+1}"
        user = usernames[i]
        password = credentials[i]

        print(f"[{i+1}/{NUM_CLIENTS}] Launching prefix {prefix} with username '{user}'")
        launch_client(prefix, docs, title)
        time.sleep(DELAY_BETWEEN_LAUNCHES)  # wait a bit for launcher to open

        print("  Typing username (click into launcher window first!)")
        time.sleep(1)
        pyautogui.write(user, interval=USERNAME_DELAY)
        pyautogui.press("tab")  # focus password field
        time.sleep(1)

        # this will work, just need to figure out k/v store
        pyautogui.write(password, interval=USERNAME_DELAY)
        time.sleep(1)
        pyautogui.press("enter")

    print("\nAll launch attempts done. Enter passwords and click Play for each client.")
    print("Window placement must be handled via KDE Window Rules or manually.")

if __name__ == "__main__":
    run()
