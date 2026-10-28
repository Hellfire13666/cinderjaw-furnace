#!/usr/bin/env python3
"""CINDERJAW v0.2.0 — public web footprint harvester, Python 3 standard library."""
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import ipaddress
from html import escape
from html.parser import HTMLParser
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse as U
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET

VERSION='0.2.0'
AGENT='Cinderjaw'
UA='Cinderjaw/0.2.0 (public web footprint research)'
MAX_BODY=1048576
HEADERS=('server','content-type','content-security-policy','content-security-policy-report-only',
         'strict-transport-security','x-frame-options','x-content-type-options','referrer-policy',
         'permissions-policy','x-powered-by','cache-control','x-robots-tag','cross-origin-opener-policy',
         'cross-origin-resource-policy','access-control-allow-origin','location','etag','last-modified')

def utc(): return datetime.now(timezone.utc).isoformat()
def clean(value): return ''.join(c if c.isprintable() else ' ' for c in str(value))
def say(label,value):
    color=sys.stdout.isatty() and 'NO_COLOR' not in os.environ
    orange='\033[38;5;208m' if color else ''
    white='\033[0m' if color else ''
    print(f'{orange}[{label}]{white} {clean(value)}',flush=True)

def normalize(value,base=None):
    value=U.urljoin(base,value) if base else value
    p=U.urlsplit(value)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:
        raise ValueError('Use an HTTP(S) URL without credentials')
    if any(ord(c)<32 or ord(c)==127 for c in value): raise ValueError('Control character in URL')
    host=p.hostname.encode('idna').decode('ascii').lower()
    if ':' in host:
        ipaddress.IPv6Address(host)
        host='['+host+']'
    elif len(host)>253 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',label) for label in host.rstrip('.').split('.')):
        raise ValueError('Invalid hostname')
    port=p.port
    netloc=host+(f':{port}' if port and port != (443 if p.scheme=='https' else 80) else '')
    return U.urlunsplit((p.scheme.lower(),netloc,p.path or '/',p.query,''))

def origin(value):
    p=U.urlsplit(value)
    return U.urlunsplit((p.scheme,p.netloc,'','',''))

def crawlable(url):
    p=U.urlsplit(url)
    if p.query: return False
    # Avoid common action URLs, even though this collector never submits forms.
    if re.search(r'(?:^|[/_.-])(logout|logoff|signout|delete|remove|unsubscribe|checkout|cart)(?:$|[/_.-])',p.path,re.I): return False
    suffix=Path(p.path).suffix.lower()
    return suffix in ('','.html','.htm','.php','.asp','.aspx')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

class Fetcher:
    def __init__(self,timeout=8,delay=0.5,budget=20):
        self.timeout=timeout; self.delay=delay; self.budget=budget
        self.used=0; self.last=0; self.results=[]
        self.opener=urllib.request.build_opener(NoRedirect())
    def get(self,url):
        if self.used >= self.budget: raise RuntimeError('HTTP request budget reached')
        time.sleep(max(0,self.delay-(time.monotonic()-self.last)))
        self.used+=1; self.last=time.monotonic()
        row={'url':url,'time_utc':utc()}
        body=b''
        response=None
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Encoding':'identity'})
            try:
                response=self.opener.open(req,timeout=self.timeout)
            except urllib.error.HTTPError as exc:
                response=exc
            with response:
                row['status']=response.code
                row['headers']={k:response.headers.get(k) for k in HEADERS if response.headers.get(k) is not None}
                row['cookies']=[]
                for raw in response.headers.get_all('Set-Cookie',[]):
                    cookies=SimpleCookie()
                    try: cookies.load(raw)
                    except Exception: continue
                    for name,c in cookies.items():
                        row['cookies'].append({'name':name,'secure':bool(c['secure']),
                            'httponly':bool(c['httponly']),'samesite':c['samesite']})
                body=response.read(MAX_BODY+1)
                row['truncated']=len(body)>MAX_BODY
                body=body[:MAX_BODY]
                row['body_sha256']=hashlib.sha256(body).hexdigest()
                row['body_bytes_captured']=len(body)
                charset=response.headers.get_content_charset() or 'utf-8'
                try: body=body.decode(charset,errors='replace')
                except LookupError: body=body.decode('utf-8',errors='replace')
        except (OSError,ValueError) as exc:
            row['error']=str(exc)
            body=''
        self.results.append(row)
        say(str(row.get('status','FAILED')),url)
        return row,body

class Page(HTMLParser):
    def __init__(self,url):
        super().__init__(convert_charrefs=True)
        self.url=url; self.base=url; self.in_title=False; self.title=[]
        self.links=set(); self.scripts=set(); self.styles=set(); self.frames=set()
        self.forms=[]; self.metadata={}; self.canonical=[]
    def link(self,value):
        try: return normalize(value,self.base)
        except (ValueError,UnicodeError): return None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='title': self.in_title=True
        if tag=='base' and a.get('href'):
            new=self.link(a['href'])
            if new: self.base=new
        if tag=='a' and a.get('href'):
            link=self.link(a['href'])
            if link: self.links.add(link)
        if tag in ('script','iframe') and a.get('src'):
            link=self.link(a['src'])
            if link: (self.scripts if tag=='script' else self.frames).add(link)
        if tag=='link' and a.get('href'):
            link=self.link(a['href'])
            rel=(a.get('rel') or '').lower().split()
            if link and 'stylesheet' in rel: self.styles.add(link)
            if link and 'canonical' in rel: self.canonical.append(link)
        if tag=='meta':
            name=(a.get('name') or a.get('property') or '').lower()
            if name in ('description','generator','robots','og:title','og:description','og:image','og:url','twitter:card'):
                self.metadata[name]=(a.get('content') or '')[:4000]
        if tag=='form':
            action=self.link(a.get('action') or self.url)
            self.forms.append({'action':action,'method':(a.get('method') or 'GET').upper()})
    def handle_endtag(self,tag):
        if tag=='title': self.in_title=False
    def handle_data(self,data):
        if self.in_title: self.title.append(data)
    def result(self):
        return {'url':self.url,'title':''.join(self.title).strip()[:1000],
                'metadata':self.metadata,'canonical':self.canonical[:30],
                'links':sorted(self.links)[:1000],'scripts':sorted(self.scripts)[:500],
                'stylesheets':sorted(self.styles)[:500],'frames':sorted(self.frames)[:100],
                'forms':self.forms[:100],
                'truncated_lists':len(self.links)>1000 or len(self.scripts)>500 or len(self.styles)>500 or len(self.frames)>100 or len(self.forms)>100}

def sitemap(body):
    try:
        root=ET.fromstring(body)
        kind=root.tag.rsplit('}',1)[-1]
        if kind not in ('sitemapindex','urlset'): return [],'not a sitemap'
        items=[n.text.strip() for n in root.iter() if n.tag.rsplit('}',1)[-1]=='loc' and n.text]
        return items[:500],(kind+'; truncated at 500 entries' if len(items)>500 else kind)
    except ET.ParseError as exc:
        return [],str(exc)

def harvest(target,pages=5,budget=20,timeout=8,delay=0.5,fetcher=None):
    target=normalize(target); base=origin(target)
    f=fetcher or Fetcher(timeout,delay,budget)
    report={'tool':'CINDERJAW','version':VERSION,'target':target,'started_utc':utc(),
            'pages':[],'policies':[],'sitemaps':[],'skipped':[], 'request_budget':budget,
            'max_pages':pages,'limitations':[]}
    say('CINDERJAW / IGNITION',target)
    robots_url=base+'/robots.txt'
    row,body=f.get(robots_url)
    rp=urllib.robotparser.RobotFileParser(robots_url)
    if row.get('status') in (404,410): rp.parse([])
    elif row.get('status')==200 and not row.get('truncated'):
        rp.parse(body.splitlines())
    else:
        report['limitations'].append('Robots unavailable, blocked or truncated; crawl stopped.')
        return finish(report,f)
    report['policies'].append({'url':robots_url,'kind':'robots','text':body[:16000],'text_truncated':len(body)>16000})
    report['robots_delay']=rp.crawl_delay(AGENT)
    report['robots_request_rate']=str(rp.request_rate(AGENT))
    f.delay=max(f.delay,float(rp.crawl_delay(AGENT) or 0))
    rate=rp.request_rate(AGENT)
    if rate and rate.requests>0: f.delay=max(f.delay,rate.seconds/rate.requests)
    if f.delay>30:
        report['limitations'].append('Robots requested delay over 30 seconds; crawl stopped.')
        return finish(report,f)
    seen=set(); queue=deque([(target,'page'),(base+'/.well-known/security.txt','security'),
                             (base+'/sitemap.xml','sitemap')])
    for url in rp.site_maps() or []:
        try: queue.append((normalize(url,base),'sitemap'))
        except ValueError: pass
    while queue and f.used<budget:
        url,kind=queue.popleft()
        try: url=normalize(url)
        except (ValueError,UnicodeError): continue
        if url in seen: continue
        seen.add(url)
        reason=None
        if origin(url)!=base: reason='external origin; recorded only'
        elif not rp.can_fetch(AGENT,url): reason='robots disallow'
        elif kind=='page' and (len(report['pages'])>=pages or not crawlable(url)): reason='page limit or action/query/non-page URL'
        if reason:
            report['skipped'].append({'url':url,'reason':reason}); continue
        row,body=f.get(url)
        status=row.get('status',0)
        if status in (301,302,303,307,308):
            location=row.get('headers',{}).get('location')
            if location:
                try: queue.appendleft((normalize(location,url),kind))
                except ValueError: pass
            continue
        if status==429:
            report['limitations'].append('HTTP 429 received; stopped without retrying.')
            break
        if status!=200: continue
        content_type=row.get('headers',{}).get('content-type','').lower()
        if kind=='security':
            if 'text/plain' in content_type:
                report['policies'].append({'url':url,'kind':'security.txt','text':body[:16000], 'text_truncated':len(body)>16000})
                say('DISCLOSURE',url)
            else: report['limitations'].append('security.txt returned non-plain-text content; not treated as a policy.')
        elif kind=='sitemap':
            locations,note=sitemap(body)
            report['sitemaps'].append({'url':url,'locations':locations,'parse_status':note})
            nextkind='sitemap' if note.startswith('sitemapindex') else 'page'
            for loc in locations:
                try: queue.append((normalize(loc,url),nextkind))
                except ValueError: pass
        elif 'html' in content_type:
            page=Page(url)
            try: page.feed(body)
            except (ValueError,AssertionError) as exc:
                report['limitations'].append('HTML parser: '+str(exc))
            result=page.result(); report['pages'].append(result)
            say('PAGE',result['title'] or '(no title)')
            for label,key in [('SCRIPT','scripts'),('FORM','forms')]:
                for item in result[key][:10]: say(label,str(item))
            for link in result['links']: queue.append((link,'page'))
    if queue:
        report['limitations'].append('Request budget or stop condition left queued discoveries unvisited.')
    return finish(report,f)

def finish(report,fetcher):
    report['requests']=fetcher.results
    report['finished_utc']=utc()
    hosts=set()
    for p in report['pages']:
        for key in ('links','scripts','stylesheets','frames'):
            for url in p[key]:
                if origin(url)!=origin(report['target']): hosts.add(U.urlsplit(url).netloc)
    report['external_hosts']=sorted(hosts)
    report['summary']={'http_requests':fetcher.used,'pages':len(report['pages']),
        'scripts':len({v for p in report['pages'] for v in p['scripts']}),
        'forms':sum(len(p['forms']) for p in report['pages']),
        'external_hosts':len(hosts),'transport_failures':sum('error' in r for r in fetcher.results)}
    say('HARVEST',json.dumps(report['summary']))
    for host in sorted(hosts)[:30]: say('EXTERNAL HOST',host)
    for note in report['limitations']: say('LIMIT',note)
    return report

def save(report,path):
    paths=[path,path.with_suffix('.json'),path.with_suffix('.html')]
    if any(p.exists() for p in paths): raise FileExistsError('Choose a new filename; a report already exists')
    path.parent.mkdir(parents=True,exist_ok=True)
    # Render only escaped data. The HTML report has no remote resources or scripts.
    text=json.dumps(report,indent=2,ensure_ascii=True)
    human=['FICTIONAL OFFLINE DEMO — NOT LIVE FINDINGS' if report.get('demo') else 'LIVE COLLECTION SNAPSHOT', 'CINDERJAW / PUBLIC WEB FOOTPRINT',report['target'],report['started_utc'],
           'Snapshot observations; not a vulnerability verdict.',json.dumps(report['summary']), '']
    for p in report['pages']:
        human += ['PAGE '+p['url'], 'TITLE '+clean(p['title'])]
        for kind in ('metadata','canonical','scripts','stylesheets','forms','links'):
            human += [kind.upper()+': '+json.dumps(p[kind],ensure_ascii=True)]
    human += ['\nREQUEST EVIDENCE',json.dumps(report['requests'],indent=2,ensure_ascii=True),
              '\nPOLICIES',json.dumps(report['policies'],indent=2,ensure_ascii=True),
              '\nSITEMAPS',json.dumps(report['sitemaps'],indent=2,ensure_ascii=True),
              '\nSKIPPED / LIMITATIONS',json.dumps(report['skipped'],indent=2,ensure_ascii=True),
              json.dumps(report['limitations'],ensure_ascii=True)]
    human='\n'.join(human)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>CINDERJAW evidence</title><style>body{background:#101112;color:#eee7d7;font:16px/1.65 monospace;margin:0}main{max-width:1100px;margin:auto;padding:30px}h1{font-size:clamp(30px,7vw,64px);letter-spacing:3px;color:#ff7524}h2{color:#ff7524}header{border-bottom:4px solid #ff7524}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#191b1c;padding:20px;border-left:3px solid #ff7524}small{color:#b5b2a9}</style><main><header><small>GLITCHBYTE PHANTOM LABS / TOOL 02</small><h1>CINDERJAW</h1><p>PUBLIC WEB FOOTPRINT / EVIDENCE REPORT</p></header>'''
    html+='<h2>'+escape(report['target'])+'</h2><pre>'+escape(human)+'</pre><small>Static observations, not proof of vulnerability. No JavaScript was executed during collection.</small></main></html>'
    for p,content in zip(paths,[human,text,html]):
        with p.open('x',encoding='utf-8') as f: f.write(content)
    say('SAVED',' / '.join(str(p) for p in paths))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('target',help='Domain or full HTTP(S) URL')
    ap.add_argument('--pages',type=int,default=5,help='Maximum HTML pages, 1–30')
    ap.add_argument('--budget',type=int,default=20,help='Maximum HTTP requests including redirects, 4–100')
    ap.add_argument('--timeout',type=float,default=8)
    ap.add_argument('--delay',type=float,default=0.5)
    ap.add_argument('-o','--output',type=Path,help='New .txt report; also writes .json and .html')
    args=ap.parse_args()
    if not (1<=args.pages<=30 and 4<=args.budget<=100 and 1<=args.timeout<=60 and 0.5<=args.delay<=30):
        ap.error('Limits: pages 1–30, budget 4–100, timeout 1–60, delay 0.5–30 seconds')
    if args.output and args.output.suffix.lower()!='.txt': ap.error('-o must end in .txt')
    if args.output and any(p.exists() for p in (args.output,args.output.with_suffix('.json'),args.output.with_suffix('.html'))): ap.error('Report exists; choose a new filename')
    target=args.target if '://' in args.target else 'https://'+args.target
    try: target=normalize(target)
    except (ValueError,UnicodeError) as exc: ap.error(str(exc))
    report=harvest(target,args.pages,args.budget,args.timeout,args.delay)
    if args.output: save(report,args.output)
    if report['summary']['transport_failures']: return 1
    return 0 if report['pages'] else 2

if __name__=='__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:
        print('\nStopped. Interrupted collection was not saved.',file=sys.stderr); sys.exit(130)
    except (OSError,ValueError,RuntimeError) as exc:
        print('Error: '+clean(exc),file=sys.stderr); sys.exit(2)
