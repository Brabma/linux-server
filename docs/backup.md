# Záchrana denní zálohy

## Situace

Tablet drží nasbíraná data jen několik dní, potom je maže. Zálohy uzavřených dnů se proto stahují na počítač při každé aktualizaci přehledu. Záloha za 11. října 2026 se po Wi-Fi přerušila a na počítači zůstal jen neúplný soubor.

## Postup

Neúplný soubor zůstal stranou, nic se nepřepisovalo ani nemazalo. Nový přenos proběhl po kabelu (USB) a než nahradil běžnou zálohu, prošel těmito kontrolami:

1. Kontrolní součet souboru na tabletu se shoduje se součtem na počítači.
2. Soubor jde celý rozbalit a končí závěrečným záznamem.
3. Počet záznamů odpovídá manifestu exportu z tabletu.
4. Databáze obnovená ze zálohy projde kontrolou neporušenosti.
5. Nechybí žádná ze čtvrthodinových dávek.

## Výsledek

| Údaj | Hodnota |
|---|---:|
| Záznamů za 11. 10. 2026 UTC | 188 521 |
| Dávek (96 v každé ze dvou řad) | 192 ze 192 |
| Velikost zálohy | 76 MB |
| Velikost obnovené databáze | 342 MB |
| Kontrola databáze | v pořádku |

Stejně se na počítač zálohují i provozní soubory a databáze tabletu; každá databáze prochází kontrolou zvlášť.

## Kontrola obnovitelnosti

- Stažený soubor ještě není záloha. Zálohou je až ve chvíli, kdy z něj jde data obnovit.
- Neúplný pokus se nemaže, dokud není hotová ověřená náhrada.
- Pro velké přenosy se vyplatí druhá cesta, tady kabel.

## Opakování kontroly

Skript [verify_archive.py](../scripts/verify_archive.py) používá jen standardní knihovnu Pythonu. Nad uloženou samostatnou kopií ověří oba kontrolní součty, rozbalení archivu, závěrečný záznam, počty řádků, `quick_check` a všech 192 očekávaných dávek. Do dat nezapisuje.

```sh
python scripts/verify_archive.py /cesta/k/ulozenemu/dni
```

[Ukázka výstupu](../examples/archive-verification.json) pochází z opakované kontroly skutečného archivu za 11. října. Úspěch znamená neporušenou uloženou kopii a úplnost dávek, nikoli zachycení všech zpráv světa.
