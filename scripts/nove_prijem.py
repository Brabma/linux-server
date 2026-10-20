"""Přijímač „Nové od…“ na VPS. Spouští ho jen vynucený příkaz klíče tabletu (authorized_keys: restrict,command=…).

Ze stdin (nejvýš 16 kB) vezme nejvýš 5 položek s titulkem a odkazem, doplní čas přijetí podle serveru a atomicky
zapíše nove.json, který Nginx vydá jako /nove.json. Argumenty ani SSH_ORIGINAL_COMMAND nečte. Poškozený vstup
odmítne a starý soubor nechá být (stránka pak po 45 min ukáže, že kontrola stojí). Položku s odkazem mimo
sledované redakce vynechá (ANSA veřejné přebírání nepovoluje, proto chybí), ostatní zapíše.
"""
import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

TARGET = Path('/srv/svet-public/nove/nove.json')
# Redakce, které detektor sleduje (od 18. 10. i titulky v původním jazyce); doména i její subdomény.
DOMAINS = {'ceskenoviny.cz', 'irozhlas.cz', 'sme.sk', 'dennikn.sk', 'teraz.sk', 'tagesschau.de', 'orf.at', 'tvn24.pl',
           'bbc.co.uk', 'bbc.com', 'dw.com', 'npr.org', 'un.org', 'euronews.com', 'cbc.ca', 'scmp.com', 'japantimes.co.jp',
           'allafrica.com', 'rfi.fr', 'kyivindependent.com', 'lemonde.fr', 'elpais.com', 'agenciabrasil.ebc.com.br',
           'focustaiwan.tw', 'antaranews.com', 'yna.co.kr', 'nannews.ng', 'app.com.pk', 'qna.org.qa',
           'aljazeera.com', 'theguardian.com', 'france24.com'}
LIMIT, MAX_ITEMS = 16384, 5      # nejvýš 16 kB vstupu a 5 položek v pruhu


def allowed(host):
    return bool(host) and any(host == d or host.endswith('.' + d) for d in DOMAINS)


def when(value, now):
    t = dt.datetime.fromisoformat(str(value))
    if t.tzinfo is None or t > now + dt.timedelta(minutes=10):
        raise ValueError('čas')
    return t.astimezone(dt.timezone.utc).isoformat()


def clean(raw, now):
    if len(raw) > LIMIT:
        raise ValueError('velikost')
    data = json.loads(raw)
    items = data['items']
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ValueError('položky')
    out, skipped = [], 0
    for i in items:
        title = ' '.join(str(i['title']).split())
        if not 5 <= len(title) <= 200 or re.search(r'[<>\x00-\x1f\x7f]', title):
            raise ValueError('titulek')
        url = str(i['url'])
        p = urlsplit(url)
        if (p.scheme != 'https' or p.port or p.username or p.password
                or len(url) > 300 or re.search(r'[\s"\'<>\\]', url)):
            raise ValueError('odkaz')
        first = when(i['first'], now)
        published = when(i.get('published') or i['first'], now)      # čas vydání článku (od 18. 10.)
        if not allowed(p.hostname):
            skipped += 1; continue
        out.append(dict(title=title, url=url, first=first, published=published))
    return dict(at=when(data['at'], now), received_at=now.isoformat(), items=out), skipped


def write(result, target=TARGET):
    fd, temp = tempfile.mkstemp(prefix='.nove-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(json.dumps(result, ensure_ascii=False).encode('utf8'))
            f.flush()
            os.fsync(f.fileno())
        os.chmod(temp, 0o644)
        os.replace(temp, target)
    except BaseException:
        if os.path.exists(temp):
            os.unlink(temp)
        raise


def main(stdin=sys.stdin.buffer, target=TARGET, now=None):
    raw = stdin.read(LIMIT + 1)
    try:
        result, skipped = clean(raw.decode('utf8'), now or dt.datetime.now(dt.timezone.utc))
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        print('ODMÍTNUTO ' + type(exc).__name__, file=sys.stderr)
        return 2
    write(result, target)
    print('OK' + (' vynecháno %d' % skipped if skipped else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
