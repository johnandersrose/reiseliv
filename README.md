# Reiseliv

AI-drevet planlegger for bilbaserte rundreiser i Norge. Kjernesløyfen:

> Preferanser → ruteforslag i tre varianter («raskeste / billigste / vakreste»)
> → dag-for-dag-plan med aktiviteter, overnatting og spisesteder → booking →
> støtte under reisen → evaluering som forbedrer personaliseringen.

Prosjektet er i planleggingsfasen. Ingen applikasjonskode ennå.

## Innhold

| Fil | Hva |
|---|---|
| [`docs/backlog.md`](docs/backlog.md) | Strukturert produktbacklog: 155 brukerhistorier, dedupliserte, med IDs, MoSCoW-prioritering og MVP-scope |
| [`docs/mvp-spec.md`](docs/mvp-spec.md) | MVP-spesifikasjon: avgrensning, datamodell, scoringsmotor, API-skisse, teknologiforslag |
| [`docs/brukerhistorier-original.txt`](docs/brukerhistorier-original.txt) | Originale brukerhistorier (ekstrahert fra *Brukerhistorier_kopi.docx*) |
| [`spike/RESULTS.md`](spike/RESULTS.md) | Datafeasibility-spike: finnes åpne datakilder for de tre rutevariantene? **(Konklusjon: GO)** |
| [`spike/oslo_bergen_spike.py`](spike/oslo_bergen_spike.py) | Kjørbart spike-skript (kun standardbibliotek) |

## Status

- [x] Backlog strukturert og prioritert (27 Must-historier definerer MVP)
- [x] MVP-spec med datamodell rundt «3 varianter»-sløyfen
- [x] Datakilder verifisert (SSB live; NVDB/NOBIL/MET/OSM kilde-verifisert)
- [ ] Juridisk GDPR-avklaring (se 🚩 DATA-02 i backlogen)
- [ ] Teknisk oppsett: Valhalla + PostGIS med Norge-data
