# Overzicht ondersteunde invoer voor `parse_time_range`

Dit document beschrijft (zo compleet mogelijk) welke zinnen, patronen en combinaties de parser kan verwerken voor het bepalen van een **tijd-range**: `(start, end)`.

> Notatie:
>
> - "Hele dag" = `00:00:00` t/m `23:59:59` (seconds-only)
> - "default duur" = `default_minutes` (standaard 60 minuten) wanneer alleen een starttijd gegeven is
> - Default timezone = `Europe/Amsterdam` (IANA)

---

## Table of Contents

1. [Relatieve dagen (NL/EN)](#1-relatieve-dagen-nlen)
2. [Relatieve dag + tijd (NL/EN)](#2-relatieve-dag--tijd-nlen)
3. [Weekdagen (NL/EN)](#3-weekdagen-nlen)
4. [Weekdagen met modifiers (NL/EN)](#4-weekdagen-met-modifiers-nlen)
5. [Weekdag + tijd](#5-weekdag--tijd)
6. [Periodes (week/maand/jaar) (NL/EN)](#6-periodes-weekmaandjaar-nlen)
7. [Expliciete tijdranges (NL/EN)](#7-expliciete-tijdranges-nlen)
8. [Datumbereiken](#8-datumbereiken-tussen--en--van--tot-)
9. [Ranges over middernacht](#9-ranges-over-middernacht)
10. [Losse tijdstippen (zonder datum)](#10-losse-tijdstippen-zonder-datum)
11. [Nederlandse spreektaal-tijden (heuristisch)](#11-nederlandse-spreektaal-tijden-heuristisch)
12. [ISO datums](#12-iso-datums)
13. [Europese datums (DD-MM-YYYY / DD/MM/YYYY)](#13-europese-datums-dd-mm-yyyy--ddmmyyyy)
14. [Maandnamen (NL + afkortingen)](#14-maandnamen-nl--afkortingen)
15. [Engelse maandnamen](#15-engelse-maandnamen)
16. [Datums "in een zin" (extractie)](#16-datums-in-een-zin-extractie)
17. [Duur-aanduidingen](#17-duur-aanduidingen)
18. [Kwartalen (NL/EN)](#18-kwartalen-nlen)
19. [Feestdagen (fixed)](#19-feestdagen-fixed)
20. [Feestdagen (bewegend, o.b.v. Pasen)](#20-feestdagen-bewegend-obv-pasen)
21. [Ordinale weekdagen](#21-ordinale-weekdagen-bijv-eerste-maandag-van-maart)
22. [Parameters](#parameters)
23. [Returnwaarden](#returnwaarden)
24. [Bekende beperkingen & heuristiek](#bekende-beperkingen--heuristiek)

---

## 1) Relatieve dagen (NL/EN)

| Invoer        | Resultaat            | Opmerkingen |
| ------------- | -------------------- | ----------- |
| `vandaag`     | hele dag vandaag     |             |
| `morgen`      | hele dag morgen      |             |
| `overmorgen`  | hele dag overmorgen  |             |
| `gisteren`    | hele dag gisteren    |             |
| `eergisteren` | hele dag eergisteren |             |
| `today`       | hele dag vandaag     | EN          |
| `tomorrow`    | hele dag morgen      | EN          |
| `yesterday`   | hele dag gisteren    | EN          |

### Varianten / extra woorden

| Invoer        | Resultaat         | Opmerkingen                         |
| ------------- | ----------------- | ----------------------------------- |
| `vandaag nog` | hele dag vandaag  | extra woorden worden vaak genegeerd |
| `morgen aub`  | hele dag morgen   |                                     |
| `gister`      | hele dag gisteren | als vocab/pattern dit dekt          |

---

## 2) Relatieve dag + tijd (NL/EN)

| Invoer             | Resultaat                           |
| ------------------ | ----------------------------------- |
| `morgen 15:00`     | morgen 15:00 → 16:00 (default duur) |
| `vandaag 14:30`    | vandaag 14:30 → 15:30               |
| `overmorgen 10:00` | overmorgen 10:00 → 11:00            |
| `morgen 9 uur`     | morgen 09:00 → 10:00                |
| `morgen 9u`        | morgen 09:00 → 10:00                |
| `tomorrow 3pm`     | morgen 15:00 → 16:00                |
| `today 9am`        | vandaag 09:00 → 10:00               |

### Dagdelen (afhankelijk van dateparser/locale settings)

| Invoer           | Resultaat           | Opmerkingen |
| ---------------- | ------------------- | ----------- |
| `morgen ochtend` | range in de ochtend | heuristiek  |
| `morgen middag`  | range in de middag  | heuristiek  |
| `morgen avond`   | range in de avond   | heuristiek  |
| `vrijdag nacht`  | range ’s nachts     | heuristiek  |

---

## 3) Weekdagen (NL/EN)

| Invoer              | Resultaat                         |
| ------------------- | --------------------------------- | --- |
| `maandag`           | eerstvolgende maandag, hele dag   |
| `dinsdag`           | eerstvolgende dinsdag, hele dag   |
| `woensdag`          | eerstvolgende woensdag, hele dag  |
| `donderdag`         | eerstvolgende donderdag, hele dag |
| `vrijdag`           | eerstvolgende vrijdag, hele dag   |
| `zaterdag`          | komende zaterdag, hele dag        |
| `zondag`            | komende zondag, hele dag          |
| `monday` … `sunday` | idem                              | EN  |

---

## 4) Weekdagen met modifiers (NL/EN)

| Invoer               | Resultaat               | Opmerkingen                    |
| -------------------- | ----------------------- | ------------------------------ |
| `volgende maandag`   | maandag volgende week   |                                |
| `volgende dinsdag`   | dinsdag volgende week   |                                |
| `komende woensdag`   | komende woensdag        |                                |
| `aanstaande vrijdag` | aanstaande vrijdag      |                                |
| `deze maandag`       | maandag in huidige week | als nog “logisch” t.o.v. `now` |
| `this monday`        | maandag in huidige week | EN                             |
| `next monday`        | maandag volgende week   | EN                             |
| `last friday`        | vorige vrijdag          | EN                             |
| `vorige vrijdag`     | vorige vrijdag          | NL                             |

---

## 5) Weekdag + tijd

| Invoer               | Resultaat                           |
| -------------------- | ----------------------------------- |
| `woensdag 10 uur`    | woensdag 10:00 → 11:00              |
| `vrijdag 14:30`      | vrijdag 14:30 → 15:30               |
| `maandag 9am`        | maandag 09:00 → 10:00               |
| `dinsdag 3pm`        | dinsdag 15:00 → 16:00               |
| `next friday at 3pm` | vrijdag volgende week 15:00 → 16:00 |

---

## 6) Periodes (week/maand/jaar) (NL/EN)

| Invoer                                            | Resultaat                              |
| ------------------------------------------------- | -------------------------------------- | --- |
| `deze week`                                       | ma 00:00 → zo 23:59:59 (huidige week)  |
| `volgende week`                                   | ma 00:00 → zo 23:59:59 (volgende week) |
| `komende week`                                    | als “volgende week”                    |     |
| `vorige week` / `afgelopen week` / `laatste week` | vorige week (ma→zo)                    |     |
| `deze maand`                                      | 1e 00:00 → laatste dag 23:59:59        |
| `volgende maand`                                  | 1e volgende maand → laatste dag        |
| `vorige maand` / `afgelopen maand`                | vorige maand                           |     |
| `dit jaar`                                        | 1 jan → 31 dec (hele dag-einden)       |
| `volgend jaar`                                    | 1 jan volgend jaar → 31 dec            |
| `vorig jaar` / `afgelopen jaar`                   | vorig jaar                             |     |
| `this week/month/year`                            | EN varianten                           |     |
| `next week/month/year`                            | EN varianten                           |     |
| `last week/month/year`                            | EN varianten                           |     |

---

## 7) Expliciete tijdranges (NL/EN)

| Invoer                | Resultaat                                      |
| --------------------- | ---------------------------------------------- |
| `van 10:00 tot 12:30` | vandaag 10:00 → 12:30                          |
| `van 9 tot 17 uur`    | vandaag 09:00 → 17:00                          |
| `van 9 uur tot 5 uur` | vandaag 09:00 → 17:00 (interpreteert 5 als 17) |
| `van 14:00 tot 15:30` | vandaag 14:00 → 15:30                          |
| `from 10:00 to 12:00` | vandaag 10:00 → 12:00                          |
| `from 9am to 5pm`     | vandaag 09:00 → 17:00                          |
| `from 9 to 17`        | vandaag 09:00 → 17:00                          |

### “Tussen … en …” (tijd)

| Invoer                  | Resultaat             |
| ----------------------- | --------------------- |
| `tussen 14:00 en 15:30` | vandaag 14:00 → 15:30 |
| `tussen 9 en 12 uur`    | vandaag 09:00 → 12:00 |
| `tussen 10:00 en 11:00` | vandaag 10:00 → 11:00 |

---

## 8) Datumbereiken (“tussen … en …”, “van … tot …”)

| Invoer                         | Resultaat                    | Opmerkingen |
| ------------------------------ | ---------------------------- | ----------- |
| `tussen maandag en woensdag`   | ma 00:00 → wo 23:59:59       | hele dagen  |
| `van maandag tot vrijdag`      | ma 00:00 → vr 23:59:59       | hele dagen  |
| `tussen 1 en 5 februari`       | 1 feb 00:00 → 5 feb 23:59:59 |             |
| `van 1 januari tot 31 januari` | hele maand januari           |             |

---

## 9) Ranges over middernacht

| Invoer                | Resultaat                    | Opmerkingen   |
| --------------------- | ---------------------------- | ------------- |
| `van 22:00 tot 02:00` | vandaag 22:00 → morgen 02:00 | dag-correctie |
| `van 23:00 tot 01:00` | vandaag 23:00 → morgen 01:00 |               |
| `from 11pm to 2am`    | vandaag 23:00 → morgen 02:00 | EN            |

---

## 10) Losse tijdstippen (zonder datum)

| Invoer  | Resultaat             | Opmerkingen       |
| ------- | --------------------- | ----------------- |
| `9:30`  | vandaag 09:30 → 10:30 | default duur      |
| `14:00` | vandaag 14:00 → 15:00 |                   |
| `9.30`  | vandaag 09:30 → 10:30 | `.` als scheiding |
| `9am`   | vandaag 09:00 → 10:00 | EN                |
| `3pm`   | vandaag 15:00 → 16:00 | EN                |
| `9 uur` | vandaag 09:00 → 10:00 | NL                |
| `9u`    | vandaag 09:00 → 10:00 | NL                |

---

## 11) Nederlandse spreektaal-tijden (heuristisch)

| Invoer          | Resultaat (typisch)  | Opmerkingen           |
| --------------- | -------------------- | --------------------- |
| `kwart over 9`  | 09:15 → 10:15        | heuristiek            |
| `half 10`       | 09:30 → 10:30        | NL: half tien = 09:30 |
| `kwart voor 10` | 09:45 → 10:45        | heuristiek            |
| `morgen half 3` | morgen 14:30 → 15:30 |                       |

---

## 12) ISO datums

| Invoer       | Resultaat             |
| ------------ | --------------------- |
| `2025-11-01` | 1 nov 2025, hele dag  |
| `2026-03-15` | 15 mrt 2026, hele dag |
| `2025-12-25` | 25 dec 2025, hele dag |

---

## 13) Europese datums (DD-MM-YYYY / DD/MM/YYYY)

| Invoer       | Resultaat             |
| ------------ | --------------------- |
| `15-03-2026` | 15 mrt 2026, hele dag |
| `01/02/2026` | 1 feb 2026, hele dag  |
| `25-12-2025` | 25 dec 2025, hele dag |

---

## 14) Maandnamen (NL + afkortingen)

### Voluit

| Invoer           | Resultaat                      |
| ---------------- | ------------------------------ |
| `5 januari`      | 5 jan (huidig of volgend jaar) |
| `5 januari 2026` | 5 jan 2026                     |
| `1 februari`     | 1 feb (huidig of volgend jaar) |
| `15 maart`       | 15 mrt                         |
| `op 15 maart`    | 15 mrt (tekst eromheen mag)    |
| `25 december`    | 25 dec                         |

### Afkortingen

| Invoer   | Resultaat   |
| -------- | ----------- |
| `5 jan`  | 5 januari   |
| `1 feb`  | 1 februari  |
| `15 mrt` | 15 maart    |
| `10 apr` | 10 april    |
| `25 dec` | 25 december |

---

## 15) Engelse maandnamen

| Invoer             | Resultaat |
| ------------------ | --------- |
| `5 january`        | 5 jan     |
| `1 february`       | 1 feb     |
| `15 march`         | 15 mrt    |
| `1 may`            | 1 mei     |
| `4 july`           | 4 jul     |
| `31 october`       | 31 okt    |
| `fifth of january` | 5 jan     |
| `1st of march`     | 1 mrt     |
| `on 1st of march`  | 1 mrt     |

---

## 16) Datums “in een zin” (extractie)

| Invoer                              | Resultaat                    |
| ----------------------------------- | ---------------------------- |
| `wat is het maximum op 2025-11-01?` | 1 nov 2025                   |
| `statistieken voor 2025-12-25`      | 25 dec 2025                  |
| `afspraken op 15 maart`             | 15 mrt (huidig/volgend jaar) |
| `meeting op dinsdag`                | komende dinsdag              |

---

## 17) Duur-aanduidingen

| Invoer                  | Resultaat                                | Opmerkingen                |
| ----------------------- | ---------------------------------------- | -------------------------- |
| `30 minuten` / `30 min` | nu → nu+30 min                           |                            |
| `2 uur`                 | nu → nu+2 uur                            | **ambigu** (zie hieronder) |
| `3 dagen`               | vandaag 00:00 → dag+3 23:59:59 (typisch) | implementatie-afhankelijk  |
| `1 week` / `2 weken`    | nu/andaag → +1/+2 weken                  |                            |
| `1 maand` / `3 maanden` | nu/andaag → +1/+3 maanden                |                            |
| `1 jaar`                | nu/andaag → +1 jaar                      |                            |

### Verschuivingen (in/over/geleden)

| Invoer         | Resultaat               | Opmerkingen |
| -------------- | ----------------------- | ----------- |
| `in 2 dagen`   | over 2 dagen (datum)    |             |
| `over 3 weken` | over 3 weken (datum)    |             |
| `2 weeks ago`  | 2 weken geleden (datum) |             |
| `3 days ago`   | 3 dagen geleden (datum) |             |

### Duur + datum-context

| Invoer              | Resultaat                          | Opmerkingen        |
| ------------------- | ---------------------------------- | ------------------ |
| `morgen 30 minuten` | morgen (tijd heuristisch) + 30 min |                    |
| `morgen 2 uur`      | kan 02:00 betekenen of 2 uur duur  | context/heuristiek |

---

## 18) Kwartalen (NL/EN)

| Invoer             | Resultaat                  | Opmerkingen               |
| ------------------ | -------------------------- | ------------------------- |
| `Q1`               | kwartaal 1 van huidig jaar |                           |
| `Q4 2025`          | kwartaal 4 van 2025        |                           |
| `eerste kwartaal`  | Q1 huidig jaar             | NL                        |
| `4e kwartaal 2025` | Q4 2025                    | NL                        |
| `kwartaal 2`       | Q2 huidig jaar             | NL                        |
| `quarter 3 2026`   | Q3 2026                    | EN (als pattern dit dekt) |
| `1st quarter 2025` | Q1 2025                    | EN                        |
| `first quarter`    | Q1 huidig jaar             | EN                        |

---

## 19) Feestdagen (fixed)

De parser kan vaste feestdagen herkennen (op basis van `FIXED_HOLIDAYS` vocab), zoals:

- `nieuwjaar`
- `koningsdag`
- `kerst` / `eerste kerstdag` / `tweede kerstdag` (afhankelijk van vocab)
- etc.

### Voorbeelden

| Invoer       | Resultaat                                |
| ------------ | ---------------------------------------- |
| `kerst`      | 25 dec (huidig/volgend jaar) hele dag    |
| `koningsdag` | 27 april (huidig/volgend jaar) hele dag  |
| `nieuwjaar`  | 1 januari (huidig/volgend jaar) hele dag |

---

## 20) Feestdagen (bewegend, o.b.v. Pasen)

De parser kan bewegende feestdagen herkennen (op basis van `MOVING_HOLIDAYS` + `MOVING_HOLIDAY_PATTERN`), zoals:

- `pasen` (Eerste Paasdag)
- `tweede paasdag` (Easter + 1)
- `goede vrijdag` (Easter - 2)
- `hemelvaartsdag` (Easter + 39)
- `pinksteren` (Easter + 49)
- `tweede pinksterdag` (Easter + 50)
- `carnaval` (Easter - 49)
- `aswoensdag` (Easter - 46)

### Voorbeelden

| Invoer            | Resultaat                             |
| ----------------- | ------------------------------------- |
| `pasen`           | eerstvolgende Pasen, hele dag         |
| `pasen 2026`      | Pasen 2026, hele dag                  |
| `goede vrijdag`   | eerstvolgende Goede Vrijdag, hele dag |
| `hemelvaart 2027` | Hemelvaart 2027, hele dag             |
| `carnaval`        | eerstvolgende Carnaval, hele dag      |

---

## 21) Ordinale weekdagen (bijv. “eerste maandag van maart”)

Ondersteuning (als pattern aanwezig) voor ordinalen + weekdag + maand/relatieve periode:

| Invoer                         | Resultaat           | Opmerkingen       |
| ------------------------------ | ------------------- | ----------------- |
| `eerste maandag van maart`     | die datum, hele dag |                   |
| `tweede dinsdag van februari`  | die datum, hele dag |                   |
| `laatste vrijdag van de maand` | die datum, hele dag | relatief op `now` |

---

## Parameters

| Parameter         | Type                           | Default              | Beschrijving                                   |
| ----------------- | ------------------------------ | -------------------- | ---------------------------------------------- |
| `text`            | `str`                          | verplicht            | De te parsen tekst                             |
| `now`             | `datetime`/`pendulum.DateTime` | verplicht (intern)   | Referentietijdstip voor relatieve berekeningen |
| `default_minutes` | `int`                          | `60`                 | Standaard duur als alleen starttijd gegeven is |
| `tz`              | `str`                          | `"Europe/Amsterdam"` | IANA timezone                                  |

> MCP tools gebruiken meestal `timezone` i.p.v. `tz` en zetten `now` intern.

---

## Returnwaarden

De parser retourneert conceptueel een tuple `(start, end)`.

**Tijdregels:**

- Alleen datum / dag-range / feestdag / periode: `00:00:00` → `23:59:59`
- Datum + tijd: `start` exact → `start + default_minutes`
- Expliciete range: `start` → `end`
- Over middernacht: `end` kan op volgende dag vallen
- **Seconds-only output** (geen microseconds)

---

## Bekende beperkingen & heuristiek

1. **Ambigu “2 uur”**
   Kan betekenen: `02:00` óf “duur: 2 uur”.
   In sommige contexten kiest de parser tijd (02:00) als er een datumcontext is.

2. **Spreektaal (“half 10”, “kwart over …”)**
   Werkt heuristisch en kan verschillen per locale/dateparser-instellingen.

3. **Rond jaarwisseling**
   “deze week/volgende week” kan verrassend zijn afhankelijk van ISO-weekregels.

4. **Taal-mixen**
   “next maandag” kan misgaan. Gebruik consequent NL of EN.

5. **Onbekende tekst**
   Gooit meestal `ValueError` met: `Kon tekst niet parsen: ...`
