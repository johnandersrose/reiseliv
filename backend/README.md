# Reiseliv backend

FastAPI-skjelett som implementerer MVP-sløyfen fra
[`../docs/mvp-spec.md`](../docs/mvp-spec.md): preferanser → tre rutevarianter
→ dagsplan → kostnader → redigering/regenerering → valg → evaluering.

## Kjør

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload      # API på http://localhost:8000/docs
python -m pytest tests/ -q         # 9 ende-til-ende-tester
```

Eksempel:

```bash
curl -X POST localhost:8000/trips -H 'Content-Type: application/json' -d '{
  "origin": {"name": "Oslo", "lat": 59.9139, "lon": 10.7522},
  "destination": {"name": "Bergen", "lat": 60.3913, "lon": 5.3221},
  "start_date": "2026-08-01", "days": 3
}'
```

## Arkitektur

- `app/models.py` – datamodellen fra spec kap. 2 (SQLAlchemy; SQLite i dev,
  Postgres/PostGIS i produksjon).
- `app/providers/` – all geografi bak grensesnitt: `StubRoutingProvider`
  (syntetiske ruter, dev/test) og `ValhallaRoutingProvider` (produksjon, velges
  med `ROUTING_PROVIDER=valhalla`, se `../infra/`). POI-korridorsøk i
  `StubPoiProvider` byttes til PostGIS `ST_DWithin` senere.
- `app/generator.py` – scoringsmotoren (spec kap. 3): én pipeline, tre
  målfunksjoner, grådig dagsplanlegger som aldri bryter harde begrensninger.
- `app/enrichment.py` – ruteberikelse: bompenger (NVDB objekttype 45),
  fergesjablong og scenic-score (andel Nasjonale turistveger +
  viewpoint-tetthet). Ekte data hentes med `scripts/fetch_nvdb_data.py`
  (objekttype-ID-er slås opp ved navn i datakatalogen); uten dem brukes
  `data/*.sample.*` (grove tilnærminger for dev/test).
- `app/main.py` – REST-endepunktene fra spec kap. 4. Auth er ikke med i
  skjelettet (én dev-bruker).

Drivstoffpriser er SSB-månedssnitt (2026M05) som konstanter; i produksjon
oppdateres de av en batchjobb mot SSB tabell 09654.

## Bevisste skjelett-forenklinger

- Ingen auth/brukere utover dev-bruker — magic link kommer med BRUK-09.
- Berikelsen bruker sample-data til `scripts/fetch_nvdb_data.py` er kjørt
  lokalt (sandkasser når ikke NVDB); provideren logger advarsel om dette.
- Fergetakster vedlikeholdes manuelt (ingen åpen API, se `../spike/RESULTS.md` #4).
- Aktivitets-/overnattingspriser er sjablonger merket `is_estimate`.
