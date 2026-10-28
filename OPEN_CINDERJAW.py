#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import uuid
root=Path(__file__).resolve().parent
print('CINDERJAW / FURNACE EDITION\nGlitchByte Phantom Labs\n\n1. Live harvest\n2. Offline demo + saved sample reports\n3. Run tests\n4. Open easy recipes\n5. Compare two saved JSON reports')
choice=input('Choose [1]: ').strip() or '1'
cmd=None
if choice=='1':
    domain=input('Domain or full URL: ').strip()
    cmd=[sys.executable,str(root/'cinderjaw_harvester.py'),domain]
    if input('Deeper collection: up to 20 pages / 60 requests? [y/N]: ').strip().lower()=='y': cmd+=['--pages','20','--budget','60']
    if input('Save TXT, JSON and HTML? [y/N]: ').strip().lower()=='y':
        p=Path.home()/'CinderjawReports'/('cinderjaw-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.txt')
        cmd+=['-o',str(p)]
elif choice=='2':
    p=Path.home()/'CinderjawReports'/('cinderjaw-FICTIONAL-demo-'+uuid.uuid4().hex[:8]+'.txt')
    cmd=[sys.executable,str(root/'DEMO_CINDERJAW.py'),'-o',str(p)]
elif choice=='3': cmd=[sys.executable,'-m','unittest','-v']
elif choice=='5':
    before=input('BEFORE JSON file path: ').strip()
    after=input('AFTER JSON file path: ').strip()
    p=Path.home()/'CinderjawReports'/('cinderjaw-diff-'+uuid.uuid4().hex[:8]+'.txt')
    cmd=[sys.executable,str(root/'cinderjaw_diff.py'),before,after,'-o',str(p)]
elif choice=='4':
    print((root/'EASY_RECIPES.md').read_text())
else: print('Unknown choice.')
if cmd:
    result=subprocess.run(cmd,cwd=root)
    print('Exit status:',result.returncode)
    if choice=='2' and result.returncode==0 and input('Open fictional HTML report in browser? [y/N]: ').strip().lower()=='y':
        try: subprocess.run(['xdg-open',str(p.with_suffix('.html'))],check=False)
        except OSError as exc: print('Open the HTML file manually:',p.with_suffix('.html'))
input('Press Enter to close...')
