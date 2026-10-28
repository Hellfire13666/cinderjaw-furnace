# CINDERJAW v0.2.0 — Furnace Edition

![CINDERJAW](assets/cinderjaw-mark.svg)

**Tool 2 / GlitchByte Phantom Labs Cultivation Room**

A public web footprint harvester with burnt-orange live output and a bone-white-on-charcoal evidence report. Independent from MAILTHORN, RosieRiot Overdrive and every existing lab tool. Entry point: `cinderjaw_harvester.py`. Python 3.9+ standard library only; no pip or API keys. It retrieves public web content directly, so collection requests are visible to the website.

## ONE-PASTE INSTALL & OPEN
Download `CINDERJAW-FURNACE-v0.2.0.zip` to Downloads. Paste this entire block into your MX Linux / Ubuntu terminal:

```bash
cd "$HOME/Downloads" &&
python3 -m zipfile -e CINDERJAW-FURNACE-v0.2.0.zip "$HOME/PhantomLabsTools" &&
cd "$HOME/PhantomLabsTools/cinderjaw-v0.2.0" &&
python3 -m unittest -q &&
python3 INSTALL_DESKTOP.py &&
python3 OPEN_CINDERJAW.py
```

Requires installed Python 3.9+. No sudo needed. Creates an independent versioned app-menu/desktop launcher. The desktop may ask you to allow launching. Keep the installed folder in place. Re-running restores packaged files in this version's tool folder; reports stay separately in `~/CinderjawReports`.

## New: AFTERBURN comparison

Compare two CINDERJAW collection JSON reports from the same exact target URL. No network requests. Reports list newly observed and not-observed-again scripts, stylesheets, frames, forms, links, pages and external hosts. Compare policy text and selected security/technology headers on shared successful responses. Each report includes both snapshots' coverage, failures, truncation and limits; missing observations are not labeled deleted or vulnerable.

The comparison's TXT/JSON/HTML outputs include input file paths and SHA256 hashes. Input snapshots are not changed. Collector versions v0.1.0 and v0.2.0 share the supported collection schema. This is a structural inventory diff, not byte-for-byte page comparison or a security verdict. Policy comparisons only cover files present in both snapshots; other policy presence changes can be checked in source reports. Header absence is an observation; request failures are excluded from header comparisons. It accepts reports up to 25 MiB each and requires matching exact target strings. Differences in ordering are ignored; same URLs are deduplicated.

Menu option **5** asks for BEFORE and AFTER JSON file paths and saves a comparison. A fully fictional pair and a sample comparison are included in `examples/`. Preview artwork is preserved in `assets/CINDERJAW-concept-preview.png`; its v0.1.0 label describes the original concept, not a screenshot of v0.2.0.

## Choose your bite

[18 easy copy-and-paste recipes](EASY_RECIPES.md): change the first DOMAIN line, then paste the block. The interactive menu also asks for a domain, deeper collection, and report saving.

- **IGNITION:** start at robots.txt, then the requested public page.
- **PAGE:** titles, canonical URLs, metadata, public links, scripts, stylesheets, frames and form actions/methods.
- **DISCLOSURE:** collect published `/.well-known/security.txt` as plain text.
- **SITEMAPS:** read sitemap.xml and robots-declared sitemaps; follow sitemap indexes within the request budget.
- **HARVEST:** unique script count, form count across pages, external hosts, and request failures.
- **EVIDENCE:** selected response/security headers, cookie names/flags without values, HTTP status, URL, timestamp, captured-body hash, truncation markers, and skipped URLs.

Forms are recorded, never submitted. Script URLs are recorded, not downloaded/executed. Third-party asset/profile hosts are listed, not crawled. Header presence/absence is an observation, not a vulnerability score. Cookie parsing is best-effort; no cookie values are retained or sent back. Each fetch is an independent unauthenticated GET with no cookie session.

## Reports
`-o NAME.txt` writes TXT, JSON, and a self-contained HTML evidence report. Live terminal output continues while collecting. HTML has escaped content and no remote assets/scripts. Open the HTML in Firefox if desired; it is an evidence document, not a dashboard. Report files are exclusive-create to protect earlier evidence. If writing fails, one or two report files may remain; use a fresh basename for retry.

Default: 5 HTML pages / 20 total requests, at least 0.5 seconds between starts, 8-second per-request timeout. Deeper recipe: 20 pages / 60 requests. Maximum: 30 pages / 100 requests. Redirect requests count toward the budget. Robots crawl-delay/request-rate can increase the wait; requested delays over 30 seconds stop collection. HTTP 429 stops without retry. Robots failures, 401/403 and truncated robots stop collection; 404/410 allow it. Uses Python's robotparser interpretation, not a claim of full RFC 9309 conformance.

## Scope and honest limits

Only the exact HTTP(S) origin is crawled. Redirects to a different scheme, port, or hostname are recorded and not followed; rerun with the known canonical public URL after reviewing it. This includes common redirects from a bare domain to www. No automatic HTTP fallback when HTTPS fails.

Discovery excludes query URLs and common action paths, and does not click buttons or submit forms. This filter is a heuristic, not a guarantee about website behavior. It performs no directory guessing, vulnerability exploitation, authentication, or JavaScript rendering. Linked binary files and query URLs may be inventoried but are not crawled as pages. Nonstandard file extensions may be skipped. security.txt presence is not full RFC 9116 signature/expiry validation. Legacy root security.txt is not fetched in this prototype.

HTML links are limited to 1000 per page, scripts/styles to 500 each, frames/forms to 100 each. Sitemaps store up to 500 locations per file. Responses capture at most 1 MiB; raw HTML bodies are not retained. SHA256 describes captured bytes, not necessarily an entire response when truncated. Only selected headers are retained. UTF-8 is assumed when the HTTP charset is absent; HTML charset metadata is not used. Compressed responses are not decompressed if a server ignores Accept-Encoding: identity. Binary sitemap.gz files are not supported. Names/hosts discovered in content are not proof of ownership. DNS/TLS are handled by Python's normal HTTP client and certificate validation, not separately enumerated.

This is bounded collection, not all available intelligence. Requests may time out; operating-system DNS resolution can outlast socket timeouts. Interrupting does not save a partial run. Missing records/pages and transport failures remain distinct. Limits and queued discoveries left unvisited are reported.

## Demo and verification
`DEMO_CINDERJAW.py` uses fictional fixtures with no network calls. It demonstrates 5 HTTP fixture requests, 2 HTML pages, 1 script URL, 1 form, 2 external hosts, robots exclusions and a disclosure policy. Optional generated demo reports are clearly marked fictional.

22 tests passed (14 collector tests plus 8 comparison tests): URL canonicalization/validation, action/query filtering, HTML extraction, base-URL handling, sitemap parsing/capping, robots compliance, request budget, unavailable-robots stop, escaped reports/overwrite protection, cross-origin redirect/429 stop tests, plus a real local HTTP server test verifying redirect recording and cookie-value omission. Local transport tests do not prove internet connectivity or MX desktop integration. The build-environment remote smoke test timed out at robots.txt and stopped with an explicit transport failure. Successful remote collection is not yet verified on your computer. Not published to GitHub.

Exit codes: 0 = at least one page collected with no transport failures; 1 = transport failure(s); 2 = no pages/argument/file error; 130 = interrupted. HTTP 4xx/5xx remain response statuses in evidence rather than transport failures; inspect the report and limitations.

## One practical next improvement
Add a compact request-status comparison, keeping redirects and failed responses distinct from successful page observations.

## References
- https://docs.python.org/3/library/urllib.robotparser.html
- https://docs.python.org/3/library/urllib.request.html
- https://www.rfc-editor.org/rfc/rfc9116.html
