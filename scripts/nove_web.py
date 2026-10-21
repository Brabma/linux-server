"""Běží na tabletu: pošle stav pruhu „Nové od…“ na veřejný web (mujlinux.cloud), aby bylo vidět, kdy aktualizovat přehled.

Klíč tabletu má na serveru vynucený příkaz nove_prijem.py: smí jen předat tento soubor, nic jiného.
Bez nove-web.json (vedle skriptu) se nic neposílá. Chyba přenosu se jen vrátí do logu, detektor běží dál.
nove-web.json: {"target": "uživatel@server", "key": "cesta ke klíči", "known_hosts": "cesta k known_hosts"}
"""
import json
import subprocess
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / 'nove-web.json'


def payload(data):
    # Server přijme jen titulek, odkaz, čas zachycení (first) a vydání článku (published); interní klíče zůstávají na tabletu.
    return dict(at=data['at'], items=[dict(title=i['title'], url=i['url'], first=i['first'], published=i.get('published') or i['first'])
                                      for i in data['items'] if str(i.get('url') or '').startswith('https://')])


def push(data, run=subprocess.run):
    if not CONFIG.exists(): return 'VYPNUTO'
    try:
        c = json.loads(CONFIG.read_text(encoding='utf8'))
        args = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
                '-o', 'UserKnownHostsFile=' + c['known_hosts'], '-i', c['key'], c['target']]
        r = run(args, input=json.dumps(payload(data), ensure_ascii=False), capture_output=True, text=True,
                encoding='utf8', timeout=40)
    except Exception as exc:
        return 'CHYBA ' + type(exc).__name__
    # „OK vynecháno 1“: server zapsal stav, jen položku z redakce mimo veřejný seznam (ANSA) nevydal.
    out = (r.stdout or '').strip()
    return out if r.returncode == 0 and out.startswith('OK') else 'CHYBA %d %s' % (r.returncode, (r.stderr or '').strip()[-120:])
