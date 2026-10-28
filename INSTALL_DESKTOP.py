#!/usr/bin/env python3
"""Create versioned local app-menu and desktop launchers, without sudo."""
from pathlib import Path
import os
import shutil
import subprocess
root=Path(__file__).resolve().parent
# Desktop Exec requires double-quoted paths with its own escape rules.
def quote(value):
    return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')+'"'
runner=root/'OPEN_CINDERJAW.py'
entry='\n'.join(['[Desktop Entry]','Type=Application','Name=CINDERJAW — Furnace Edition v0.2.0',
    'Comment=GlitchByte Phantom Labs public web footprint intel',
    'Exec=python3 '+quote(runner),'Terminal=true','Icon=utilities-terminal','Categories=Utility;Network;',''])
apps=Path.home()/'.local/share/applications'
apps.mkdir(parents=True,exist_ok=True)
locations=[apps/'glitchbyte-cinderjaw-v020.desktop']
try:
    desktop=Path(subprocess.check_output(['xdg-user-dir','DESKTOP'],text=True).strip())
except (OSError,subprocess.CalledProcessError):
    desktop=Path.home()/'Desktop'
if desktop.is_dir() and desktop != Path.home():
    locations.append(desktop/'glitchbyte-cinderjaw-v020.desktop')
for path in locations:
    if path.exists():
        if path.read_text() == entry:
            print('Already installed:',path)
            continue
        raise SystemExit('Launcher already exists with different contents: '+str(path))
    with path.open('x') as f: f.write(entry)
    path.chmod(0o755)
    print('Created:',path)
print('Keep this extracted tool folder in place. Your desktop may ask you to allow launching.')
