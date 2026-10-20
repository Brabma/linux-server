import datetime as dt
import gzip
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from verify_archive import sha256, verify


class ArchiveChecks(unittest.TestCase):
    def fixture(self, folder, missing=False, trailer=True):
        root = Path(folder)
        day = dt.datetime(2026, 10, 11)
        rows = [[stream, (day + dt.timedelta(minutes=15 * i)).strftime('%Y%m%d%H%M%S'), 'ok']
                for stream in ('english', 'translated') for i in range(96)]
        if missing:
            rows.pop()
        db = root / 'experiment.sqlite'
        connection = sqlite3.connect(db)
        connection.execute('CREATE TABLE gdelt_docs(url TEXT)')
        connection.execute('CREATE TABLE gdelt_batches(stream TEXT, stamp TEXT, status TEXT)')
        connection.executemany('INSERT INTO gdelt_batches VALUES (?,?,?)', rows)
        connection.commit()
        connection.close()
        counts = dict(gdelt_docs=0, gdelt_batches=len(rows))
        manifest = dict(format=1, day_utc='2026-10-11', complete=True, counts=counts)
        archive = root / 'day.jsonl.gz'
        with gzip.open(archive, 'wt', encoding='utf-8') as out:
            out.write(json.dumps(manifest) + '\n')
            for row in rows:
                out.write(json.dumps(['gdelt_batches', row]) + '\n')
            if trailer:
                out.write(json.dumps(dict(end=True, counts=counts)) + '\n')
        manifest.update(sha256=sha256(db), transfer_sha256=sha256(archive))
        (root / 'manifest.json').write_text(json.dumps(manifest))
        return root

    def test_complete_saved_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertTrue(verify(self.fixture(folder))['passed'])

    def test_false_complete_flag_cannot_hide_missing_batch(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'coverage'):
                verify(self.fixture(folder, missing=True))

    def test_missing_trailer_rejected_even_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'trailer'):
                verify(self.fixture(folder, trailer=False))

    def test_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(folder)
            with (root / 'day.jsonl.gz').open('ab') as out:
                out.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'Checksum'):
                verify(root)


if __name__ == '__main__':
    unittest.main()
