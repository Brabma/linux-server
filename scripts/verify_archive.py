"""Read-only verification of an exported GDELT UTC day. Python standard library only.

Usage: python scripts/verify_archive.py ARCHIVE_DIRECTORY
Requires manifest.json, day.jsonl.gz and a standalone experiment.sqlite.
Never opens a live database or executes SQL supplied by the archive.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8-sig'))
    database, archive = folder / 'experiment.sqlite', folder / 'day.jsonl.gz'
    if any(Path(str(database) + suffix).exists() for suffix in ('-wal', '-shm', '-journal')):
        raise ValueError('Use a closed standalone backup without journal sidecars')
    if sha256(database) != manifest['sha256'] or sha256(archive) != manifest['transfer_sha256']:
        raise ValueError('Checksum mismatch')
    counts = {'gdelt_docs': 0, 'gdelt_batches': 0}
    with gzip.open(archive, 'rt', encoding='utf-8') as stream:
        header = json.loads(next(stream))
        if header.get('format') != 1 or header['day_utc'] != manifest['day_utc']:
            raise ValueError('Export format or day mismatch')
        ended = False
        for line in stream:
            if ended:
                raise ValueError('Records after trailer')
            item = json.loads(line)
            if isinstance(item, dict):
                if item.get('end') is not True or item.get('counts') != counts:
                    raise ValueError('Invalid trailer')
                ended = True
            else:
                table, row = item
                if table not in counts or not isinstance(row, list):
                    raise ValueError('Unexpected record')
                counts[table] += 1
        if not ended or counts != manifest['counts']:
            raise ValueError('Missing trailer or wrong counts')
    day = dt.date.fromisoformat(manifest['day_utc'])
    start = dt.datetime.combine(day, dt.time(), dt.timezone.utc)
    expected = {(stream, (start + dt.timedelta(minutes=15 * i)).strftime('%Y%m%d%H%M%S'))
                for stream in ('english', 'translated') for i in range(96)}
    connection = sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        integrity = [row[0] for row in connection.execute('PRAGMA quick_check')]
        stored_counts = {table: connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                         for table in counts}  # table names are the fixed allowlist above
        batches = list(connection.execute('SELECT stream, stamp, status FROM gdelt_batches'))
        actual = {(stream, stamp) for stream, stamp, status in batches if status == 'ok'}
        if integrity != ['ok'] or stored_counts != counts:
            raise ValueError('Database integrity or count mismatch')
        if actual != expected or len(batches) != len(expected):
            raise ValueError('Incomplete or unexpected batch coverage')
        if manifest.get('complete') is not True or header.get('complete') is not True:
            raise ValueError('Export is marked incomplete')
        return dict(day_utc=day.isoformat(), passed=True, records=counts['gdelt_docs'],
                    expected_batches=len(expected), verified_batches=len(actual), quick_check=integrity,
                    archive_sha256=manifest['transfer_sha256'], database_sha256=manifest['sha256'],
                    scope='Saved archive integrity and batch coverage; not global news completeness')
    finally:
        connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.directory), indent=2))
    except (ValueError, KeyError, OSError, EOFError, sqlite3.Error) as error:
        raise SystemExit('Verification failed: ' + type(error).__name__)
