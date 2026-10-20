"""Odeslání „Nové od…“ na veřejný web: jen přes vynucený příkaz, bez sítě v testu."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nove_web

DATA = dict(at='2026-10-17T12:00:00+00:00', items=[
    dict(term='zachar', title='Trump naznačil, že jeho nová mluvčí končí', url='https://www.irozhlas.cz/x', first='2026-10-17T11:30:00+00:00', seen='x'),
    dict(term='bez', title='Bez odkazu', url=None, first='2026-10-17T11:00:00+00:00', seen='x')])


class Push(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name) / 'nove-web.json'
        p = patch.object(nove_web, 'CONFIG', self.config); p.start(); self.addCleanup(p.stop)

    def test_without_config_nothing_is_sent(self):
        self.assertEqual(nove_web.push(DATA, run=lambda *a, **k: self.fail('sent')), 'VYPNUTO')

    def test_payload_has_only_public_fields(self):
        self.assertEqual(nove_web.payload(DATA), dict(at=DATA['at'], items=[dict(title=DATA['items'][0]['title'], url='https://www.irozhlas.cz/x',
                                                                                 first='2026-10-17T11:30:00+00:00', published='2026-10-17T11:30:00+00:00')]))
        with_time = dict(DATA, items=[dict(DATA['items'][0], published='2026-10-17T10:05:00+00:00')])
        self.assertEqual(nove_web.payload(with_time)['items'][0]['published'], '2026-10-17T10:05:00+00:00')

    def test_strict_ssh_and_result(self):
        self.config.write_text(json.dumps(dict(target='web@example.cz', key='/k', known_hosts='/kh')), encoding='utf8')
        calls = []
        def run(args, **kw):
            calls.append((args, kw)); return subprocess.CompletedProcess(args, 0, 'OK\n', '')
        self.assertEqual(nove_web.push(DATA, run=run), 'OK')
        args, kw = calls[0]
        self.assertIn('StrictHostKeyChecking=yes', args); self.assertIn('BatchMode=yes', args); self.assertIn('UserKnownHostsFile=/kh', args)
        self.assertEqual(args[-1], 'web@example.cz')      # žádný příkaz: na serveru běží jen vynucený přijímač
        self.assertEqual(json.loads(kw['input']), nove_web.payload(DATA))

    def test_refusal_and_timeout_are_logged_not_raised(self):
        self.config.write_text(json.dumps(dict(target='t', key='k', known_hosts='kh')), encoding='utf8')
        self.assertTrue(nove_web.push(DATA, run=lambda a, **k: subprocess.CompletedProcess(a, 2, '', 'ODMÍTNUTO odkaz')).startswith('CHYBA 2'))
        def slow(*a, **k): raise subprocess.TimeoutExpired('ssh', 40)
        self.assertEqual(nove_web.push(DATA, run=slow), 'CHYBA TimeoutExpired')


if __name__ == '__main__':
    unittest.main()
