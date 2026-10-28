#!/usr/bin/env python3
"""Compare two CINDERJAW JSON snapshots offline; no network requests."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import sys
from cinderjaw_harvester import utc, say, clean

NOTICE=('Snapshot differences are observations, not proof of removal or vulnerability. '
        'Page limits, failed requests, robots rules and collection settings affect coverage.')

def validate(r):
    if not isinstance(r,dict) or r.get('tool')!='CINDERJAW': raise ValueError('Expected a CINDERJAW collection JSON report')
    if not isinstance(r.get('target'),str): raise ValueError('Missing target URL')
    for key in ('pages','requests','policies','limitations','external_hosts'):
        if not isinstance(r.get(key),list): raise ValueError('Invalid '+key+' list')
    for p in r['pages']:
        if not isinstance(p,dict) or not isinstance(p.get('url'),str): raise ValueError('Invalid page')
        for key in ('links','scripts','stylesheets','frames','forms'):
            if not isinstance(p.get(key),list): raise ValueError('Invalid page '+key)
            if key!='forms' and not all(isinstance(x,str) for x in p[key]): raise ValueError('Invalid URL inventory')
        if not all(isinstance(x,dict) and isinstance(x.get('action'),(str,type(None))) and isinstance(x.get('method'),str) for x in p['forms']): raise ValueError('Invalid form inventory')
    for q in r['requests']:
        if not isinstance(q,dict) or not isinstance(q.get('url'),str) or not isinstance(q.get('headers',{}),dict): raise ValueError('Invalid request evidence')
    for p in r['policies']:
        if not isinstance(p,dict) or not isinstance(p.get('url'),str) or not isinstance(p.get('text'),str): raise ValueError('Invalid policy evidence')
    if not all(isinstance(x,str) for x in r['external_hosts']): raise ValueError('Invalid host inventory')
    return r

def load(path):
    if path.stat().st_size>25*1024*1024: raise ValueError('Snapshot exceeds 25 MiB')
    return validate(json.loads(path.read_text(encoding='utf-8')))

def items(r,key):
    if key=='pages': return {p['url'] for p in r['pages']}
    if key=='external_hosts': return set(r[key])
    if key=='forms':
        return {json.dumps({'page':p['url'],'action':f['action'],'method':f['method']},sort_keys=True)
                for p in r['pages'] for f in p[key]}
    return {v for p in r['pages'] for v in p[key]}

def compare(before,after):
    validate(before); validate(after)
    if before['target']!=after['target']: raise ValueError('Targets differ. Compare reports from the same exact target URL.')
    changes={}
    for key in ('pages','scripts','stylesheets','frames','forms','links','external_hosts'):
        a,b=items(before,key),items(after,key)
        changes[key]={'newly_observed':sorted(b-a),'not_observed_again':sorted(a-b)}
    policies=[]
    a={p['url']:p for p in before['policies']}; b={p['url']:p for p in after['policies']}
    for url in sorted(a.keys() & b.keys()):
        if a[url]['text']!=b[url]['text']:
            policies.append({'url':url,'before':a[url]['text'],'after':b[url]['text'],
                             'partial_capture':bool(a[url].get('text_truncated') or b[url].get('text_truncated'))})
    headers=[]
    a={r['url']:r for r in before['requests']}; b={r['url']:r for r in after['requests']}
    for url in sorted(a.keys() & b.keys()):
        if a[url].get('status')!=200 or b[url].get('status')!=200: continue
        av,bv=a[url].get('headers',{}),b[url].get('headers',{})
        # Dynamic ETag/cache timestamps cause noise; compare security/technology observations.
        relevant={'server','x-powered-by','content-security-policy','content-security-policy-report-only',
                  'strict-transport-security','x-frame-options','x-content-type-options','referrer-policy',
                  'permissions-policy','x-robots-tag','access-control-allow-origin',
                  'cross-origin-opener-policy','cross-origin-resource-policy'}
        for key in sorted(relevant):
            if av.get(key)!=bv.get(key): headers.append({'url':url,'header':key,'before':av.get(key),'after':bv.get(key)})
    quality=[]
    for label,r in [('before',before),('after',after)]:
        quality.append({'snapshot':label,'summary':r.get('summary'),
                        'max_pages':r.get('max_pages'),'request_budget':r.get('request_budget'),
                        'limitations':r['limitations'],
                        'truncated_responses':sum(bool(x.get('truncated')) for x in r['requests']),
                        'truncated_page_lists':sum(bool(p.get('truncated_lists')) for p in r['pages']),
                        'failed_requests':sum('error' in x or x.get('status',0)>=400 for x in r['requests'])})
    return {'tool':'CINDERJAW-DIFF','version':'0.2.0','target':before['target'],'time_utc':utc(),
            'before_time':before.get('started_utc'),'after_time':after.get('started_utc'),
            'notice':NOTICE,'fictional_data':bool(before.get('demo') or after.get('demo')),
            'inventory_changes':changes,'policy_text_changes':policies,'header_changes':headers,
            'coverage':quality}

def render(r):
    lines=['CINDERJAW / AFTERBURN COMPARISON',r['target'],r['notice']]
    if r['fictional_data']: lines.insert(0,'FICTIONAL OFFLINE DEMO DATA')
    for key,v in r['inventory_changes'].items():
        lines.append(f'\n{key.upper()}: +{len(v["newly_observed"])} newly observed / {len(v["not_observed_again"])} not observed again')
        lines+=['  NEW '+x for x in v['newly_observed']]
        lines+=['  NOT OBSERVED AGAIN '+x for x in v['not_observed_again']]
    lines+=['\nPOLICY TEXT CHANGES',json.dumps(r['policy_text_changes'],indent=2,ensure_ascii=True),
            '\nHEADER CHANGES',json.dumps(r['header_changes'],indent=2,ensure_ascii=True),
            '\nCOVERAGE',json.dumps(r['coverage'],indent=2,ensure_ascii=True),
            '\nINPUT PROVENANCE',json.dumps(r.get('inputs',{}),indent=2,ensure_ascii=True)]
    return '\n'.join(lines)

def save(r,path):
    paths=[path,path.with_suffix('.json'),path.with_suffix('.html')]
    if path.suffix.lower()!='.txt': raise ValueError('Output must end in .txt')
    if any(x.exists() for x in paths): raise FileExistsError('Output already exists; choose a new basename')
    path.parent.mkdir(parents=True,exist_ok=True)
    text=render(r)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>CINDERJAW comparison</title><style>body{background:#101112;color:#eee7d7;font:16px/1.6 monospace;margin:25px}h1{color:#ff7524}pre{white-space:pre-wrap;overflow-wrap:anywhere;border-left:4px solid #ff7524;padding:20px;background:#191b1c}</style><h1>CINDERJAW / AFTERBURN</h1><pre>'''+escape(text)+'</pre></html>'
    for p,content in zip(paths,[text,json.dumps(r,indent=2,ensure_ascii=True),html]):
        with p.open('x',encoding='utf-8') as f:f.write(content)
    say('SAVED',' / '.join(str(p) for p in paths))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('before',type=Path);ap.add_argument('after',type=Path)
    ap.add_argument('-o','--output',type=Path)
    args=ap.parse_args()
    r=compare(load(args.before),load(args.after))
    r['inputs']={label:{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                 for label,p in [('before',args.before),('after',args.after)]}
    print('\n'.join(clean(line) for line in render(r).splitlines()))
    if args.output:save(r,args.output)
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:
        say('ERROR',str(exc));sys.exit(2)
