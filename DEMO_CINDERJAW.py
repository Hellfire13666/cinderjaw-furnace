#!/usr/bin/env python3
"""Offline synthetic preview: never makes network requests."""
import argparse
from pathlib import Path
import cinderjaw_harvester as c

FIXTURES={
 '/robots.txt':('text/plain','User-agent: *\nDisallow: /private/\nSitemap: https://example.com/sitemap.xml'),
 '/':('text/html','''<html><head><title>Fictional Ember Workshop</title><meta name="generator" content="Synthetic Demo"><link rel="canonical" href="https://example.com/"><script src="https://static.example.net/forge.js"></script><link rel="stylesheet" href="/style.css"></head><body><a href="/about">About</a><a href="/private/">Private</a><a href="https://social.example.org/ember">Public profile</a><form method="post" action="/contact"></form></body></html>'''),
 '/about':('text/html','<title>About the fictional workshop</title><a href="/">Home</a>'),
 '/.well-known/security.txt':('text/plain','Contact: mailto:security@example.com\nExpires: 2030-01-01T00:00:00Z'),
 '/sitemap.xml':('application/xml','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/about</loc></url></urlset>'),
}
class DemoFetcher:
    def __init__(self): self.used=0; self.delay=0.5; self.results=[]
    def get(self,url):
        self.used+=1
        content_type,body=FIXTURES.get(c.U.urlsplit(url).path,('text/plain','Not found'))
        row={'url':url,'time_utc':c.utc(),'status':200 if c.U.urlsplit(url).path in FIXTURES else 404,
             'headers':{'content-type':content_type,'server':'SYNTHETIC DEMO'},'cookies':[],
             'truncated':False,'source':'OFFLINE FICTIONAL FIXTURE'}
        self.results.append(row); c.say('DEMO',url)
        return row,body

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('-o',type=Path,help='New .txt demo report, plus JSON and HTML')
    args=ap.parse_args()
    print('OFFLINE DEMO / FICTIONAL DATA / NO NETWORK REQUESTS')
    report=c.harvest('https://example.com/',fetcher=DemoFetcher())
    report['demo']='FICTIONAL OFFLINE DATA, NOT LIVE FINDINGS'
    report['limitations'].insert(0,'FICTIONAL OFFLINE DEMO — NOT LIVE FINDINGS')
    if args.o: c.save(report,args.o)
    return report
if __name__=='__main__': main()
