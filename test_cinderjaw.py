import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
import cinderjaw_harvester as c
from DEMO_CINDERJAW import DemoFetcher

class Tests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(c.normalize('https://EXAMPLE.com:443/a#x'),'https://example.com/a')
        self.assertEqual(c.normalize('../b','https://example.com/a/x'),'https://example.com/b')
    def test_credentials_and_schemes(self):
        for url in ('file:///etc/passwd','https://u:p@example.com/','javascript:alert(1)','https://example.com/\n'):
            with self.assertRaises(ValueError): c.normalize(url)
    def test_action_filter(self):
        for url in ('https://example.com/logout','https://example.com/a?delete=1','https://example.com/p.pdf'):
            self.assertFalse(c.crawlable(url))
        self.assertTrue(c.crawlable('https://example.com/about'))
    def test_html_extraction(self):
        p=c.Page('https://example.com/')
        p.feed('<title>A &amp; B</title><script src="//cdn.example.net/x.js"></script><form action="/send" method="post"></form><meta name="generator" content="demo">')
        r=p.result()
        self.assertEqual(r['title'],'A & B')
        self.assertEqual(r['forms'][0]['action'],'https://example.com/send')
        self.assertEqual(r['scripts'],['https://cdn.example.net/x.js'])
    def test_base_url(self):
        p=c.Page('https://example.com/')
        p.feed('<base href="https://cdn.example.net/path/"><a href="next">Next</a>')
        self.assertIn('https://cdn.example.net/path/next',p.result()['links'])
    def test_sitemap(self):
        urls,kind=c.sitemap('<sitemapindex><sitemap><loc>https://example.com/part.xml</loc></sitemap></sitemapindex>')
        self.assertEqual(kind,'sitemapindex'); self.assertEqual(len(urls),1)
        self.assertFalse(c.sitemap('bad xml')[0])
    def test_sitemap_cap(self):
        urls,note=c.sitemap('<urlset>'+('<url><loc>https://example.com/</loc></url>'*501)+'</urlset>')
        self.assertEqual(len(urls),500); self.assertIn('truncated',note)
    def demo(self,**kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return c.harvest('https://example.com/',fetcher=DemoFetcher(),**kwargs)
    def test_demo_robots_and_hosts(self):
        r=self.demo()
        self.assertEqual(r['summary']['pages'],2)
        self.assertEqual(r['summary']['forms'],1)
        self.assertEqual(r['summary']['external_hosts'],2)
        self.assertTrue(any(s['reason']=='robots disallow' for s in r['skipped']))
        self.assertFalse(any('/private/' in q['url'] for q in r['requests']))
    def test_budget(self):
        r=self.demo(budget=4)
        self.assertEqual(r['summary']['http_requests'],4)
        self.assertTrue(r['limitations'])
    def test_missing_robots_stops(self):
        f=DemoFetcher()
        def fail(url):
            f.used+=1; row={'url':url,'error':'offline'};f.results.append(row); return row,''
        f.get=fail
        with contextlib.redirect_stdout(io.StringIO()): r=c.harvest('https://example.com/',fetcher=f)
        self.assertEqual(r['summary']['http_requests'],1); self.assertFalse(r['pages'])
    def test_reports_escape_and_protect(self):
        r=self.demo(); r['pages'][0]['title']='<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            p=Path(d)/'report.txt'; c.save(r,p)
            html=p.with_suffix('.html').read_text()
            self.assertIn('&lt;script&gt;',html)
            self.assertNotIn('<script>',html)
            self.assertEqual(json.loads(p.with_suffix('.json').read_text())['summary']['pages'],2)
            with self.assertRaises(FileExistsError): c.save(r,p)
    def test_real_http_transport_local_fixture(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*a): pass
            def do_GET(self):
                self.send_response(302 if self.path=='/redirect' else 200)
                self.send_header('Content-Type','text/plain')
                self.send_header('Set-Cookie','session=SECRET; HttpOnly; Secure; SameSite=Lax')
                if self.path=='/redirect': self.send_header('Location','https://external.example/')
                self.end_headers(); self.wfile.write(b'fixture')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            f=c.Fetcher(delay=0,budget=2)
            with contextlib.redirect_stdout(io.StringIO()):
                r,b=f.get(f'http://127.0.0.1:{server.server_port}/redirect')
            self.assertEqual(r['status'],302)
            self.assertEqual(f.used,1)
            self.assertNotIn('SECRET',json.dumps(r))
            self.assertTrue(r['cookies'][0]['secure'])
        finally:
            server.shutdown(); server.server_close(); thread.join()


class StopTests(unittest.TestCase):
    def test_cross_origin_redirect_recorded_not_followed(self):
        f=DemoFetcher(); old=f.get
        def redirected(url):
            if url=='https://example.com/':
                f.used+=1; row={'url':url,'status':302,'headers':{'location':'https://www.example.com/'}}
                f.results.append(row); return row,''
            return old(url)
        f.get=redirected
        with contextlib.redirect_stdout(io.StringIO()): r=c.harvest('https://example.com/',fetcher=f)
        self.assertTrue(any(s['url']=='https://www.example.com/' for s in r['skipped']))
        self.assertFalse(any(q['url']=='https://www.example.com/' for q in r['requests']))
    def test_rate_limit_stops(self):
        f=DemoFetcher(); old=f.get
        def limited(url):
            if url.endswith('/robots.txt'): return old(url)
            f.used+=1; row={'url':url,'status':429,'headers':{}}
            f.results.append(row); return row,''
        f.get=limited
        with contextlib.redirect_stdout(io.StringIO()): r=c.harvest('https://example.com/',fetcher=f)
        self.assertEqual(f.used,2)
        self.assertTrue(any('429' in note for note in r['limitations']))

if __name__=='__main__': unittest.main()
