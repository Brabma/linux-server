# Přenosy na tablet se zastavují

## Příznak

Webová stránka se přímo na tabletu načetla celá, zatímco některá čtení z počítače skončila neúplným tělem odpovědi. Potíže se objevily také při stahování větších souborů z internetu.

## Porovnání cest, 12. října 2026

| Zkouška | Výsledek |
|---|---|
| Tentýž soubor GDELT z téhož internetového serveru | PC: 4 360 336 B za 0,688 s; tablet: 650 420 B za 20,104 s, timeout během těla odpovědi |
| Stejná syntetická data PC → tablet přes USB | Celých 4 MiB za 2,484 s, kontrolní součet shodný |
| Tatáž data PC → tablet po Wi-Fi | Opakovaný přenos skončil po 15,027 s bez potvrzení celého souboru |
| Menší odpovědi po Wi-Fi i USB | Stránka přehledu (23 796 B) i 32 KiB testovací odpověď prošly po každé cestě třikrát, vždy celé |
| Večerní opakování větších přenosů | 4 MiB po Wi-Fi za 2,385 a 2,327 s; soubor GDELT celý za 0,804 s |

Úspěšné přenosy doprovází kontrolní součet obsahu. U internetového pokusu proběhlo spojení, TLS i HTTP 200; přenos na tablet se zastavil až během čtení těla.

## Závěr a provozní opatření

Porovnání zúžilo hledání na cestu k tabletu. USB zvládlo stejný objem dat, který se po Wi-Fi nedotáhl. Pro větší zálohy proto slouží jako druhá přenosová cesta. Večer už přenosy po Wi-Fi prošly. Tablet se ale mezitím restartoval, takže nejde odlišit, zda pomohl restart, nebo se změnily podmínky v síti. Další měření se zaměřují na podmínky, při kterých se závada vrací.

## Diagnostický postup

1. Zaznamenat příznak, čas a velikost odpovědi.
2. Ověřit službu přímo na zařízení.
3. Přenést stejná data dvěma cestami a porovnat obsah.
4. Oddělit vytvoření spojení od dokončení těla odpovědi.
5. Při další změně zopakovat stejné měření.
