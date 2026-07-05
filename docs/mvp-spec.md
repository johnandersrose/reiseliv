# Reiseliv – MVP-spesifikasjon

Bygger på `backlog.md` (Must-historiene, 27 stk). MVP er den tynneste
**komplette** sløyfen — ikke bredden:

> Preferanser → tre rutevarianter → dag-for-dag-plan → kostnadsoversikt →
> lagre/sammenligne → evaluering.

## 1. MVP-avgrensning

### Inne

| Kapabilitet | Dekker |
|---|---|
| Profil med reisefølge, kjøretøy, interesser, budsjett | PREF-01, OKO-01 |
| Rutegenerering fra A til B (evt. flere stopp) i tre varianter: **raskeste / billigste / vakreste** | PREF-08, PREF-09, PREF-14, BRUK-22 |
| Harde begrensninger: maks kjøretid per etappe, start-/sluttid per dag, turens lengde | PREF-21, PREF-30, SMID-05/06 |
| Dag-for-dag-plan med aktiviteter, overnatting og spisesteder i en korridor langs ruten | PREF-06, PREF-18, SMID-04 |
| Kostnadsoversikt: drivstoff, bom, ferge, overnatting (estimat), totalsum | OKO-04, OKO-05, OKO-11, OKO-14 |
| Kart + tidslinje + aktivitetsdetaljer, total reisetid | VIS-01/02/03, SMID-07, BRUK-11 |
| Manuell redigering med automatisk regenerering | BRUK-01, BRUK-12 |
| Søk på destinasjoner, lagre og sammenligne flere planer | BRUK-16, BRUK-17 |
| Evaluering etter reisen (enkel: stjerner + fritekst per plan) | DATA-01 |

### Ute (bevisst)

Booking/betaling, sanntidstilgjengelighet, tredjeparts hotell-API-er, push-varsler,
navigasjon (dyplenke til Google/Apple Maps i stedet, jf. NAV-01-notat), CarPlay,
chatbot, abonnement, gruppe, datasalg. Se `backlog.md` for begrunnelser.

### Ikke-funksjonelle krav MVP (mangler i originalbacklogen)

- **Personvern:** kun e-post + preferanser lagres; ingen kortdata, ingen
  posisjonssporing i MVP. Samtykketekst før profil-lagring. DATA-02 bygges ikke.
- **Offline:** genererte planer kan eksporteres/leses uten nett (norske fjell
  har dårlig dekning). Full offline-modus er ikke MVP, men PDF-eksport (DEL-02)
  bør trekkes tidlig inn av denne grunnen.
- **Ytelse:** generering av tre varianter < 15 s for en 7-dagers tur.

## 2. Datamodell

```
User ──1:N── TripPlan ──1:3── RouteVariant ──1:N── Leg (dag/etappe)
  │              │                                   │
  └── Preferences│                                   ├── RouteGeometry (polyline)
                 │                                   ├── N:M → Stop ── ref → Poi
                 └── Evaluation (etter reise)        └── 1:N → CostItem

Poi (katalog, delt)          Vehicle (på Preferences)
```

### Entiteter

**User** – `id, email, createdAt`. Auth via e-post/magic link i MVP (BRUK-09s
sosiale innlogginger kommer senere).

**Preferences** – `userId, party {adults, children[ages], dog}, vehicle,
interests[natur|kultur|sport|gastronomi], budgetTotalNok, maxDriveMinsPerLeg,
dayStart, dayEnd, lodgingTypes[]`. Én rad per bruker i MVP; historikk/læring
(PREF-11/27) kommer i fase 2 som en `PreferenceSignal`-hendelseslogg — design
tabellen nå, fyll den senere.

**Vehicle** – `type (ev|petrol|diesel), consumptionPer100km, tankOrBatterySize,
rangeKm?`. EV-ruting er ikke MVP, men typen lagres fra dag én (kryssnote 2 i
backlog).

**TripPlan** – `id, userId, name, origin, destination, waypoints[], startDate,
days, status (draft|chosen|completed), chosenVariantId?`. Flere per bruker
(BRUK-17).

**RouteVariant** – `tripPlanId, kind (fastest|cheapest|scenic), totalKm,
totalDriveMins, totalCostNok, scenicScore`. Alltid tre per plan; sammenligning
er å vise dem side ved side.

**Leg** – én kjøredag: `variantId, dayIndex, fromStopId, toStopId, geometry,
driveMins, km`. Bryter `maxDriveMinsPerLeg` ⇒ generatoren deler dagen.

**Stop** – `legId, poiId, kind (activity|lodging|food|rest|sight), arrival,
departure, locked (bruker-låst ved manuell redigering), order`.

**Poi** (delt katalog) – `id, name, lat, lon, category, subcategory, priceLevel,
openingHours, seasonMonths[], attributes {childFriendly, dogFriendly,
wheelchair, breakfastIncluded, …}, description, imageUrl, source, sourceId`.
Attributter som flagg-JSON: backloggen viser at nye attributter kommer løpende
(LHBT-vennlig, hundevennlig, …) — ikke skjemaendring per attributt.

**CostItem** – `variantId, legId?, kind (fuel|toll|ferry|lodging|activity|food),
amountNok, isEstimate`. Summerer til OKO-11/14; per-etappe-visning gratis.

**Evaluation** – `tripPlanId, rating 1–5, text, perStopRatings[] (valgfritt)`.
Skrives etter `status=completed`; blir treningsdata for fase 2-personalisering.

### Konfliktregler (underspesifisert i backloggen — definert her)

Prioritetsrekkefølge ved konflikt i generatoren:
1. Harde begrensninger (kjøretid/etappe, dagstider, turlengde) — brytes aldri.
2. «Må oppleves»-stopp (PREF-22, fase 2) — kan forlenge turen, aldri bryte (1).
3. Budsjettramme — overskridelse flagges rødt i UI, planen genereres likevel.
4. Interessefiltre og variant-målfunksjonen.

## 3. Scoringsmotor (tre varianter)

Alle varianter kjører samme pipeline; kun målfunksjonen endres:

```
kandidatruter (rutemotor, alternatives=true)
  → per rute: kost(rute) = w_t·tid + w_c·kroner + w_s·(1 − scenicScore)
  → raskeste: w=(1,0,0) · billigste: w=(0,1,0) · vakreste: w=(0.3,0,0.7)
  → vinnerrute per variant → korridor-POI-søk (buffer ~10 km)
  → grådig dagsplanlegging: fyll dager med stopp innenfor (1)-begrensningene,
    velg overnatting nær dagens endepunkt, spisesteder ved måltidstider
```

- `kroner` = drivstoff (km × forbruk × literpris) + bom + ferge + estimert
  overnatting per natt.
- `scenicScore` per rutesegment i MVP: andel av ruten som følger **Nasjonale
  turistveger** (18 definerte strekninger, åpne data fra Statens vegvesen) +
  tetthet av OSM-taggene `tourism=viewpoint`/`scenic=yes` i korridoren.
  Enkelt, forklarbart, godt nok til å differensiere variantene.

## 4. API-skisse (REST)

```
POST /trips                {origin, destination, waypoints?, startDate, days}
                           → genererer 3 varianter, returnerer TripPlan
GET  /trips/:id            plan med varianter, legs, stops, kostnader
PATCH /trips/:id/stops/:sid  {action: remove|lock|replace} → regenerer resten
POST /trips/:id/choose     {variantId}
GET  /trips                alle planer (lagre/sammenligne)
POST /trips/:id/evaluation {rating, text}
GET/PUT /me/preferences
GET  /pois/search          ?q= (destinasjonssøk, BRUK-16)
```

Regenerering (PATCH) beholder `locked`-stopp og kjører dagsplanleggingen på
nytt — det er dette som gjør BRUK-01 billig når pipeline-en først finnes.

## 5. Teknologiforslag (holdt bevisst kort)

- **Rutemotor:** selvhostet **OSRM** eller **Valhalla** med Geofabrik
  Norge-ekstrakt (~1,2 GB). Valhalla anbefales: innebygd støtte for
  `use_ferry`/`use_tolls`-kostnader og alternativruter. Demo-servere er kun for
  spike, ikke produksjon.
- **POI-katalog:** batch-import fra OSM (Overpass/Geofabrik) til egen
  Postgres+PostGIS-tabell. Korridorsøk = `ST_DWithin` mot rutegeometrien.
- **Backend:** én tjeneste (f.eks. Node/TypeScript eller Python/FastAPI) +
  Postgres/PostGIS. Ingen mikrotjenester i MVP.
- **Frontend:** web først (React + MapLibre GL med åpne vektorfliser).
  Mobilapp (BRUK-18) etter MVP; API-et er kontrakten.
- **Batch, ikke sanntid, i MVP:** bompriser, fergepriser, drivstoffpris-snitt og
  POI-er oppdateres som periodiske jobber. Eneste sanntidskall er selve
  rutegenereringen.

## 6. Åpne spørsmål

1. Fergepriser: AutoPASS for ferje har takstregulativ, men riksregulativets
   **persontakst ble avviklet 1.1.2025** — kun kjøretøytakst gjelder. Struktur
   finnes (Ferjedatabanken), men må vedlikeholdes halvmanuelt. Godta
   sjablongpris per fergesamband i MVP? *(Anbefaling: ja, kjøretøytakst per
   samband som sjablong.)*
2. Overnattingspriser uten booking-API: bruk prisnivå-kategori (kr/kr kr/kr kr kr)
   per POI i stedet for kronebeløp? *(Anbefaling: ja i MVP, merket `isEstimate`.)*
3. Drivstoffpris: ingen åpen norsk API funnet (se spike). Bruk landsgjennomsnitt
   fra SSB tabell 09654 i MVP-estimatet.

Se `../spike/RESULTS.md` for verifisering av datakildene.
