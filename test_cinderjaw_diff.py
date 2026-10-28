import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from DEMO_CINDERJAW import DemoFetcher
import cinderjaw_harvester as c
import cinderjaw_diff as d

class DiffTests(unittest.TestCase):
    def setUp(self):
        with contextlib.redirect_stdout(io.StringIO()):self.before=c.harvest('https://example.com/',fetcher=DemoFetcher())
        self.after=copy.deepcopy(self.before)
    def test_identical(self):
        r=d.compare(self.before,self.after)
        self.assertFalse(r['header_changes']);self.assertFalse(r['policy_text_changes'])
        self.assertTrue(all(not any(v.values()) for v in r['inventory_changes'].values()))
    def test_added_and_not_seen(self):
        self.after['pages'][0]['scripts']=['https://static.example.net/new.js']
        r=d.compare(self.before,self.after)['inventory_changes']['scripts']
        self.assertEqual(r['newly_observed'],['https://static.example.net/new.js'])
        self.assertEqual(r['not_observed_again'],['https://static.example.net/forge.js'])
    def test_form_changes(self):
        self.after['pages'][0]['forms'][0]['action']='https://example.com/new-contact'
        r=d.compare(self.before,self.after)['inventory_changes']['forms']
        self.assertEqual(len(r['newly_observed']),1)
    def test_policy_header(self):
        self.after['policies'][0]['text']+='\nDisallow: /archive'
        self.after['requests'][1]['headers']['x-frame-options']='DENY'
        r=d.compare(self.before,self.after)
        self.assertEqual(len(r['policy_text_changes']),1)
        self.assertEqual(len(r['header_changes']),1)
    def test_no_header_comparison_for_failed_response(self):
        self.after['requests'][1]['status']=500
        self.after['requests'][1]['headers']={}
        r=d.compare(self.before,self.after)
        self.assertFalse(r['header_changes'])
        self.assertEqual(r['coverage'][1]['failed_requests'],1)
    def test_target_mismatch(self):
        self.after['target']='https://other.example/'
        with self.assertRaises(ValueError):d.compare(self.before,self.after)
    def test_invalid_reports(self):
        for invalid in ({},[],{'tool':'CINDERJAW','target':'x'}):
            with self.assertRaises(ValueError):d.validate(invalid)
    def test_demo_and_escaped_output(self):
        self.after['demo']='FICTIONAL'
        self.after['pages'][0]['links'].append('https://example.com/<script>')
        r=d.compare(self.before,self.after)
        self.assertTrue(r['fictional_data'])
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            p=Path(folder)/'change.txt';d.save(r,p)
            self.assertNotIn('<script>',p.with_suffix('.html').read_text())
            self.assertIn('FICTIONAL',p.read_text())
            self.assertEqual(json.loads(p.with_suffix('.json').read_text())['tool'],'CINDERJAW-DIFF')
            with self.assertRaises(FileExistsError):d.save(r,p)

if __name__=='__main__':unittest.main()
