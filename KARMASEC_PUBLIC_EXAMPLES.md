# CINDERJAW // PUBLIC EXAMPLES

FURNACE + AFTERBURN v0.2.0
GlitchByte Phantom Labs

Test domain: https://karmasec.com/

These examples demonstrate publicly accessible website
inventory and offline snapshot comparison. Run against
websites you own or are permitted to assess.

No authentication, form submissions, exploitation, or
credential collection. Findings are observations, not
proof of vulnerabilities.

## Getting started

Install from the main README, then open the tool directory.

```bash
cd ~/PhantomLabsTools/cinderjaw-v0.2.0
```

## 1. Small live harvest

```bash
python3 cinderjaw_harvester.py https://karmasec.com/ --pages 1 --budget 6
```

## 2. Save TXT, JSON and HTML

Create a reports folder and choose a new filename.

```bash
mkdir -p reports
python3 cinderjaw_harvester.py https://karmasec.com/ --pages 1 --budget 8 -o reports/karmasec-first.txt
```

## 3. Gentle collection

Use a delay and a bounded request budget.

```bash
python3 cinderjaw_harvester.py https://karmasec.com/ --pages 2 --budget 8 --delay 3
```

## 4. Save BEFORE and AFTER snapshots

Use new filenames for each run. Existing report
files are protected from accidental overwriting.

```bash
mkdir -p reports
python3 cinderjaw_harvester.py https://karmasec.com/ --pages 1 --budget 8 -o reports/karmasec-before.txt
python3 cinderjaw_harvester.py https://karmasec.com/ --pages 1 --budget 8 -o reports/karmasec-after.txt
```

## 5. Compare with AFTERBURN

The following comparison is entirely offline.

```bash
python3 cinderjaw_diff.py reports/karmasec-before.json reports/karmasec-after.json -o reports/karmasec-afterburn.txt
```

## 6. View the HTML comparison

On a Linux desktop:

```bash
xdg-open reports/karmasec-afterburn.html
```

## Understanding the output

- HTTP 200: successful HTTP response
- HTTP 301/302: redirect response
- HTTP 404: requested resource not found
- SCRIPT: public script reference observed
- EXTERNAL HOST: linked third-party hostname
- LIMIT: unvisited discoveries due to collection limits
- TRANSPORT FAILURE: connection or retrieval error

A listed version, missing security header, or unobserved
resource is not automatically a security vulnerability.

## Verified workshop demonstration

In the October 2026 Linux workshop test, FURNACE
collected one page, 16 script references and four
external hosts from karmasec.com with zero transport
failures. Two real JSON snapshots were compared by
AFTERBURN with no inventory differences observed.

Results depend on the website and collection time.
No live output, credentials, private user files, or
personal workstation paths are included in this page.

## Important

Do not publish private report files without reviewing
their contents. The reports/ directory is excluded
from this repository by .gitignore.

See EASY_RECIPES.md for 18 additional commands.
