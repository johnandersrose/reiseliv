# Datafiler for ruteberikelse

| Fil | Innhold | Kilde |
|---|---|---|
| `toll_stations.json` | Bomstasjoner med takst | NVDB objekttype 45 (NLOD) |
| `turistveger.geojson` | Nasjonale turistveger-geometri | NVDB (NLOD) |
| `ferry_crossings.json` | Fergesamband med sjablongtakst | Vedlikeholdes manuelt (jf. spike #4) |

De ekte filene genereres med:

```bash
python3 backend/scripts/fetch_nvdb_data.py   # krever nettilgang
```

og er ikke sjekket inn (kan bli store; regenereres). Finnes ikke de ekte
filene, faller `RouteEnricher` tilbake til `*.sample.*`-filene i denne mappen —
**grove tilnærminger kun til utvikling og test**, med bevisst plasserte
negative kontroller.
