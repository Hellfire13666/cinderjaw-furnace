# CINDERJAW — Easy Recipes

Install using the README one-paste block first. Copy an entire recipe and change only DOMAIN. Use the exact canonical public hostname; cross-origin redirects are recorded but not followed. Example domains below are placeholders, not promised findings.

## 1. Standard live harvest
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" 
```

## 2. Harvest and save TXT + JSON + HTML
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" -o "$HOME/CinderjawReports/cinderjaw-$(python3 -c 'import uuid; print(uuid.uuid4().hex)').txt"
```

## 3. Deeper collection
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" --pages 20 --budget 60
```

## 4. Deeper collection and saved reports
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" --pages 20 --budget 60 -o "$HOME/CinderjawReports/cinderjaw-deep-$(python3 -c 'import uuid; print(uuid.uuid4().hex)').txt"
```

## 5. Largest supported collection budget
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" --pages 30 --budget 100
```

## 6. Small first look
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" --pages 1 --budget 6
```

## 7. Slow connection
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" --timeout 20 --delay 1
```

## 8. Gentle collection
```bash
DOMAIN="example.com"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" --pages 5 --budget 20 --delay 3
```

## 9. Plain output without color
```bash
DOMAIN="example.com"
NO_COLOR=1 python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" 
```

## 10. Start at a specific public page
```bash
DOMAIN="example.com/about"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" "$DOMAIN" --pages 3 --budget 12
```

## 11. Open friendly menu
```bash
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/OPEN_CINDERJAW.py"
```

## 12. Offline visual demo — fictional data
```bash
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/DEMO_CINDERJAW.py"
```

## 13. Save fictional demo reports
```bash
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/DEMO_CINDERJAW.py" -o "$HOME/CinderjawReports/cinderjaw-FICTIONAL-$(python3 -c 'import uuid; print(uuid.uuid4().hex)').txt"
```

## 14. Open report folder
```bash
python3 -c 'from pathlib import Path; (Path.home()/"CinderjawReports").mkdir(exist_ok=True)'
xdg-open "$HOME/CinderjawReports"
```

## 15. Show all command options
```bash
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_harvester.py" --help
```

## Reading your results

HTTP 200 means a response was returned, not that the site is secure. 301/302 are recorded redirects. 404 means the requested URL was not found. FAILED means transport failed. LIMIT explains skipped/unfinished coverage. A script, form, external host or missing header is not automatically a vulnerability. The tool does not submit forms or execute JavaScript.

## 16. Preview comparison with fictional example reports
No internet needed. Both input reports contain synthetic data, not real findings.
```bash
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_diff.py" "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/examples/demo-before.json" "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/examples/demo-after.json"
```

## 17. Compare your own saved reports
Change the two paths below to your actual JSON filenames. BEFORE is the older collection; AFTER is the newer collection. Use matching target URLs. No files are overwritten.
```bash
BEFORE="$HOME/CinderjawReports/your-older-report.json"
AFTER="$HOME/CinderjawReports/your-newer-report.json"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_diff.py" "$BEFORE" "$AFTER"
```

## 18. Compare and save TXT + JSON + HTML
```bash
BEFORE="$HOME/CinderjawReports/your-older-report.json"
AFTER="$HOME/CinderjawReports/your-newer-report.json"
python3 "$HOME/PhantomLabsTools/cinderjaw-v0.2.0/cinderjaw_diff.py" "$BEFORE" "$AFTER" -o "$HOME/CinderjawReports/cinderjaw-diff-$(python3 -c 'import uuid; print(uuid.uuid4().hex)').txt"
```
