"""Přijímač „Nové od…“ na VPS: přijme jen malé české položky, cokoli jiného odmítne a starý soubor nechá."""
import contextlib
import datetime as dt
import io
import json
import tempfile
import unittest
from pathlib import Path

import nove_prijem as n

NOW = dt.datetime(2026, 10, 17, 12, tzinfo=dt.timezone.utc)
ITEM = dict(title='Rusko zasáhlo přístav a nákladní loď, Ukrajina hlásí mrtvé i raněné',
            url='https://www.ceskenoviny.cz/zpravy/2888582', first='2026-10-17T11:40:00+00:00')
GOOD = dict(at='2026-10-17T11:59:00+00:00', items=[ITEM])


class Receiver(unittest.TestCase):
    def test_clean_keeps_only_public_fields_and_adds_server_time(self):
        out, skipped = n.clean(json.dumps(dict(GOOD, secret='x', items=[dict(ITEM, term='agency:x')])), NOW)
        self.assertEqual(out, dict(at='2026-10-17T11:59:00+00:00', received_at=NOW.isoformat(), items=[dict(ITEM, published=ITEM['first'])]))
        self.assertEqual(skipped, 0)

    def test_article_time_passed_and_checked(self):
        out, _ = n.clean(json.dumps(dict(GOOD, items=[dict(ITEM, published='2026-10-17T09:05:00+02:00')])), NOW)
        self.assertEqual(out['items'][0]['published'], '2026-10-17T07:05:00+00:00')
        with self.assertRaises(ValueError):
            n.clean(json.dumps(dict(GOOD, items=[dict(ITEM, published='zítra')])), NOW)

    def test_empty_list_is_valid_heartbeat(self):
        self.assertEqual(n.clean(json.dumps(dict(at=GOOD['at'], items=[])), NOW)[0]['items'], [])

    def test_foreign_titles_from_followed_outlets_only(self):
        # Od 18. 10. i titulky v původním jazyce; mimo sledované redakce (ANSA nepovoluje přebírání) se položka vynechá.
        ok = ['https://www.theguardian.com/world/x', 'https://domov.sme.sk/c/1', 'https://www.bbc.co.uk/news/x', 'https://en.yna.co.kr/view/x']
        skip = ['https://www.ansa.it/english/x', 'https://evil.example/ceskenoviny.cz', 'https://ceskenoviny.cz.evil.example/x', 'https://notbbc.com/x']
        out, skipped = n.clean(json.dumps(dict(GOOD, items=[dict(ITEM, url=u) for u in ok[:3]])), NOW)
        self.assertEqual([i['url'] for i in out['items']], ok[:3]); self.assertEqual(skipped, 0)
        for url in skip + ok[3:]:
            with self.subTest(url):
                out, skipped = n.clean(json.dumps(dict(GOOD, items=[dict(ITEM, url=url)])), NOW)
                self.assertEqual(len(out['items']), 1 if url in ok else 0); self.assertEqual(skipped, 0 if url in ok else 1)

    def test_rejected_inputs(self):
        bad = {'http': dict(ITEM, url='http://www.ceskenoviny.cz/x'),
               'javascript': dict(ITEM, url='javascript:alert(1)'),
               'port': dict(ITEM, url='https://www.ceskenoviny.cz:8443/x'),
               'uvozovky': dict(ITEM, url='https://www.irozhlas.cz/x"onclick'),
               'html v titulku': dict(ITEM, title='<img src=x onerror=alert(1)>'),
               'dlouhý titulek': dict(ITEM, title='x' * 201),
               'čas bez zóny': dict(ITEM, first='2026-10-17T11:40:00'),
               'čas v budoucnu': dict(ITEM, first='2026-10-18T11:40:00+00:00')}
        for name, item in bad.items():
            with self.subTest(name), self.assertRaises((ValueError, KeyError, TypeError)):
                n.clean(json.dumps(dict(GOOD, items=[item])), NOW)
        for raw in (json.dumps(dict(GOOD, items=[ITEM] * (n.MAX_ITEMS + 1))), 'x' * (n.LIMIT + 1), '[]', json.dumps(dict(at=GOOD['at']))):
            with self.subTest(raw=raw[:30]), self.assertRaises((ValueError, KeyError, TypeError)):
                n.clean(raw, NOW)

    def test_main_writes_atomically_and_refusal_keeps_old_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'nove.json'
            self.assertEqual(n.main(io.BytesIO(json.dumps(GOOD).encode()), target, NOW), 0)
            first = target.read_bytes()
            self.assertEqual(json.loads(first)['items'], [dict(ITEM, published=ITEM['first'])])
            self.assertEqual(n.main(io.BytesIO(b'{"at":"x","items":[]}'), target, NOW), 2)
            self.assertEqual(target.read_bytes(), first)
            ansa = dict(GOOD, items=[ITEM, dict(ITEM, url='https://www.ansa.it/english/x')])
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(n.main(io.BytesIO(json.dumps(ansa).encode()), target, NOW), 0)
            self.assertEqual(out.getvalue().strip(), 'OK vynecháno 1')
            self.assertEqual(json.loads(target.read_bytes())['items'], [dict(ITEM, published=ITEM['first'])])
            self.assertEqual([p.name for p in Path(folder).iterdir()], ['nove.json'])


if __name__ == '__main__':
    unittest.main()
