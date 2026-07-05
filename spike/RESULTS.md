# Spike-resultater: finnes dataene for «raskeste / billigste / vakreste»?

**Spørsmål:** Kan vi generere de tre rutevariantene for Oslo→Bergen med ekte,
åpne datakilder? (Jf. `../docs/mvp-spec.md`.)

**Konklusjon: JA – med tre presiseringer.** Alle databehov i MVP-et har en
identifisert, åpen kilde. Ingen showstoppere funnet. Presiseringene: (a)
drivstoffpris finnes bare som månedssnitt, ikke per stasjon; (b) fergetakster
må vedlikeholdes halvmanuelt; (c) overnattingspris må være nivå-estimat uten
booking-API. Alle tre er allerede håndtert som estimater i MVP-spec-en.

## Metode og forbehold

Spiken ble kjørt fra et sandkassemiljø der nettverkspolicyen blokkerer
direktekall til de fleste eksterne API-er (403 fra proxy-gateway). Derfor er
kildene verifisert på to måter:

- **Live-verifisert** – faktisk API-kall med ekte data i svar (via SSB-MCP).
- **Kilde-verifisert** – offisiell dokumentasjon/datasettregistrering bekreftet
  (lisens, tilgangsmodell, innhold), men selve API-kallet må kjøres lokalt med
  `oslo_bergen_spike.py`.

## Funn per databehov

| # | Behov (variant) | Kilde | Lisens/tilgang | Status |
|---|---|---|---|---|
| 1 | Ruting + alternativruter (alle) | OSRM demo (spike) → selvhostet **Valhalla/OSRM** med [Geofabrik Norge-ekstrakt](https://download.geofabrik.de/europe/norway.html) | ODbL (OSM) | Kilde-verifisert |
| 2 | Bomstasjoner m/ takster («billigste») | [NVDB API Les V4](https://nvdb-docs.atlas.vegvesen.no/category/nvdb-api-les-v4/), objekttype 45, jf. [datasett på data.norge.no](https://data.norge.no/en/datasets/49113c39-fefe-4141-b901-b1139d2cc767/toll-stations-in-nvdb) | **NLOD**, åpent | Kilde-verifisert |
| 3 | Drivstoffpris («billigste») | **SSB tabell 09654**, månedlig | Åpent API | ✅ **Live-verifisert:** bensin 95: **19,15 kr/l**, diesel: **20,02 kr/l** (2026M05, hentet 2026-07-05) |
| 4 | Fergetakster («billigste») | [Ferjedatabanken](https://ferjedatabanken.no/info) + AutoPASS for ferje | Åpent/registrering | Kilde-verifisert. ⚠️ Riksregulativets **persontakst ble avviklet 1.1.2025** – bruk kjøretøytakst per samband (sjablong i MVP) |
| 5 | Ladestasjoner (EL-*, fase 2) | [NOBIL via Enova](https://info.nobil.no/api), inkl. [sanntid](https://info.nobil.no/sanntid) | **CC BY 4.0**, gratis API-nøkkel fra [data.enova.no](https://data.enova.no/) | Kilde-verifisert |
| 6 | Vær langs ruten (VAER-*) | [MET locationforecast 2.0](https://api.met.no/) | Åpent, krever User-Agent m/ kontaktinfo | Kilde-verifisert |
| 7 | Scenic-score («vakreste») | [Nasjonale turistveger](https://www.nasjonaleturistveger.no/en/routes/): 18 strekninger / 2 160 km, geometri via [NVDB/Vegkart](https://www.nvdb.no/en/hente-ut-og-se-pa-data/vegkart/) + OSM `tourism=viewpoint` | NLOD + ODbL | Kilde-verifisert |
| 8 | POI-katalog (aktiviteter/spisesteder/overnatting) | OSM via Overpass/Geofabrik → egen PostGIS | ODbL | Kilde-verifisert |
| 9 | Overnattings-/aktivitetspriser | **Ingen åpen kilde.** | – | Bekreftet gap → prisnivå-estimat (`isEstimate`) i MVP, som besluttet i spec |
| 10 | Drivstoffpris per stasjon (OKO-06) | **Ingen åpen norsk API funnet** (apper som Drivstoffappen har lukkede data) | – | Bekreftet gap → OKO-06 står som Could med note i backlog |

## Regneeksempel (med live-tall)

Oslo→Bergen ≈ 460 km (E16/Rv7): `460 km × 6,5 l/100km × 19,15 kr/l ≈ 573 kr`
i drivstoff for fossilbil — «billigste»-variantens drivstoffledd er altså
beregnbart i dag med SSB-snittpris + rutedistanse. Bom og ferge legges på fra
kilde 2 og 4.

## Kjør spiken selv

```bash
python3 spike/oslo_bergen_spike.py   # krever fri internettilgang
```

Skriptet tester kildene 1–3, 6 og 7 (viewpoint-tetthet) og skriver ut et
drivstoffkost-estimat for raskeste rute.

## Anbefaling (go/no-go)

**GO.** Datagrunnlaget finnes med åpne lisenser (NLOD/ODbL/CC BY). Neste
tekniske steg er å sette opp Valhalla med Norge-ekstrakt + PostGIS med
OSM-POI-import, og implementere `scenicScore` mot Nasjonale
turistveger-geometrien — det er byggearbeid, ikke lenger usikkerhet.
