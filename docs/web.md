# Veřejný web a vydávání

Veřejný [přehled zpráv](https://mujlinux.cloud/) obsluhuje Nginx na linuxovém VPS. Tablet sbírá data, počítač připravuje vydání a na VPS jde jen hotová statická stránka a malý soubor se stavem pruhu „Nové od…“. Pro čtení přehledu nemusí být počítač zapnutý.

## Vydání stránky

1. Před přenosem kontrola odmítne interní adresy, soukromé cesty, nepovolené skripty a externí závislosti.
2. Nové vydání se nahraje vedle starého a teprve po kontrole se přepne na aktuální. Předchozí vydání zůstává pro návrat.
3. Po přenosu se stránka stáhne celá a její SHA-256 se porovná s připraveným HTML. Samotné HTTP 200 shodu nedokazuje.

Databáze, interní ovládání, přihlašovací údaje a provozní logy na veřejný server nejdou.

## Pruh „Nové od…“

Tablet každých 15 minut pošle na VPS krátký přehled nových zpráv. Na serveru má vlastní systémový účet bez hesla a jeho SSH klíč je v `authorized_keys` omezený:

```text
restrict,command="/usr/bin/python3 -I -B …/nove-prijem.py" ssh-ed25519 … svet-nove-tablet
```

Ať tablet pošle cokoli, spustí se jen přijímací skript. Ten zkontroluje formát, odmítne poškozený nebo prázdný vstup a zapíše jen soubor se stavem pruhu. `restrict` navíc vypne přesměrování portů a terminál. Když tablet 45 minut nic nepošle, stránka ukáže, že kontrola stojí, místo aby vypadala jako klid.

## HTTPS

Certifikát Let's Encrypt platí pro hlavní doménu a varianty `www` a `svet`, HTTP přesměrovává na HTTPS. Automatické obnovování je nastavené; zkušební obnova (`certbot renew --dry-run`) zatím neproběhla.

Veřejný web a tablet se kontrolují zvlášť. Výpadek spojení k tabletu neznamená, že selhal web.

[Zpět na projekt](../README.md) · [Metoda výběru zpráv](methodology.md)
