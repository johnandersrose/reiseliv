# Reiseliv

AI-drevet planlegger for bilbaserte rundreiser i Norge. Kjernesløyfen:

> Preferanser → ruteforslag i tre varianter («raskeste / billigste / vakreste»)
> → dag-for-dag-plan med aktiviteter, overnatting og spisesteder → booking →
> støtte under reisen → evaluering som forbedrer personaliseringen.

## Innhold

| Fil/mappe | Hva |
|---|---|
| [`docs/backlog.md`](docs/backlog.md) | Strukturert produktbacklog: 155 brukerhistorier, dedupliserte, med IDs, MoSCoW-prioritering og MVP-scope |
| [`docs/mvp-spec.md`](docs/mvp-spec.md) | MVP-spesifikasjon: avgrensning, datamodell, scoringsmotor, API-skisse, teknologiforslag |
| [`docs/personvern.md`](docs/personvern.md) | GDPR-avklaringsnotat (utkast til juridisk gjennomgang) |
| [`docs/brukerhistorier-original.txt`](docs/brukerhistorier-original.txt) | Originale brukerhistorier (ekstrahert fra *Brukerhistorier_kopi.docx*) |
| [`spike/RESULTS.md`](spike/RESULTS.md) | Datafeasibility-spike: finnes åpne datakilder for de tre rutevariantene? **(Konklusjon: GO)** |
| [`backend/`](backend/README.md) | FastAPI-skjelett: hele MVP-sløyfen kjører ende-til-ende med stub-ruteprovider (9 tester) |
| [`infra/`](infra/docker-compose.yml) | Valhalla + PostGIS via docker-compose; `setup.sh` laster Norge-data og bygger tiles |

## Kom i gang

```bash
cd backend && pip install -r requirements.txt
python -m pytest tests/ -q     # 9 tester, alle grønne
uvicorn app.main:app --reload  # http://localhost:8000/docs
```

Ekte rutemotor: kjør `infra/setup.sh` (lokal maskin med Docker), deretter
`ROUTING_PROVIDER=valhalla uvicorn app.main:app`.

## Status

- [x] Backlog strukturert og prioritert (27 Must-historier definerer MVP)
- [x] MVP-spec med datamodell rundt «3 varianter»-sløyfen
- [x] Datakilder verifisert (SSB live; NVDB/NOBIL/MET/OSM kilde-verifisert)
- [x] Personvernnotat skrevet (utkast) — **venter juridisk gjennomgang**
- [x] Backend-skjelett: 3-varianter-sløyfen ende-til-ende med stub-providere
- [x] Infra-oppsett for Valhalla + PostGIS (kjøres lokalt, krever Docker)
- [x] Ruteberikelse: bom (NVDB 45), ferge og scenic-score (turistveg-match) — koblet i Valhalla-provideren; `backend/scripts/fetch_nvdb_data.py` henter ekte data lokalt
- [ ] POI-import fra OSM til PostGIS (erstatter seed_pois.json)
- [ ] Kjør `infra/setup.sh` + `fetch_nvdb_data.py` lokalt og valider mot ekte Valhalla
- [ ] Auth (magic link) + frontend (React + MapLibre)
