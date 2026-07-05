#!/usr/bin/env python3
"""Henter berikelsesdata fra NVDB (Statens vegvesen, NLOD-lisens).

Skriver til backend/data/:
  - toll_stations.json   (objekttype «Bomstasjon», med takst der den finnes)
  - turistveger.geojson  (objekttype «Turistveg», linjegeometri)

Objekttype-ID-er slås opp VED NAVN i datakatalogen ved kjøring, så scriptet
er robust mot katalogendringer. Fergefilen (ferry_crossings.json)
vedlikeholdes manuelt — takstregulativet har ingen åpen API (spike #4).

Kjøres lokalt med nettilgang:  python3 backend/scripts/fetch_nvdb_data.py
Kun standardbibliotek.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BASES = [
    "https://nvdbapiles.atlas.vegvesen.no",      # v4
    "https://nvdbapiles-v3.atlas.vegvesen.no",   # fallback v3
]
HEADERS = {
    "Accept": "application/json",
    "X-Client": "reiseliv-fetch/0.1 (john.anders.rose@gmail.com)",
}


def get(base: str, path: str, **params) -> dict:
    qs = ("?" + urllib.parse.urlencode(params)) if params else ""
    req = urllib.request.Request(f"{base}{path}{qs}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def resolve_type_ids(base: str) -> dict[str, int]:
    """Finn objekttype-ID-er ved navn i datakatalogen."""
    types = get(base, "/vegobjekttyper")
    if isinstance(types, dict):
        types = types.get("vegobjekttyper") or types.get("objekter") or []
    wanted = {"bomstasjon": None, "turistveg": None}
    for t in types:
        navn = (t.get("navn") or "").strip().lower()
        if navn in wanted:
            wanted[navn] = t["id"]
    missing = [k for k, v in wanted.items() if v is None]
    if missing:
        raise SystemExit(f"Fant ikke objekttype(r) i datakatalogen: {missing}")
    print(f"  Objekttyper: {wanted}")
    return wanted


_WKT_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def parse_wkt(wkt: str) -> tuple[str, list]:
    """Minimal WKT-parser for POINT/LINESTRING (Z), srid=4326 (lon lat [z])."""
    kind = wkt.split("(", 1)[0].strip().upper().replace(" Z", "")
    coords = []
    for part in re.findall(r"\(([^()]+)\)", wkt):
        nums = [float(x) for x in _WKT_NUM.findall(part)]
        step = 3 if "Z" in wkt.split("(", 1)[0].upper() else 2
        coords.append([[nums[i], nums[i + 1]] for i in range(0, len(nums), step)])
    return kind, coords


def fetch_all(base: str, type_id: int):
    """Paginert uthenting av alle vegobjekter av en type."""
    params = {"antall": 1000, "inkluder": "egenskaper,geometri", "srid": 4326}
    start = None
    while True:
        if start:
            params["start"] = start
        data = get(base, f"/vegobjekter/{type_id}", **params)
        objekter = data.get("objekter", [])
        if not objekter:
            return
        yield from objekter
        neste = (data.get("metadata") or {}).get("neste") or {}
        start = neste.get("start")
        if not start:
            return


def egenskap(obj: dict, name_contains: str):
    for e in obj.get("egenskaper", []):
        if name_contains.lower() in (e.get("navn") or "").lower():
            return e.get("verdi")
    return None


def fetch_toll_stations(base: str, type_id: int) -> list[dict]:
    out = []
    for obj in fetch_all(base, type_id):
        wkt = (obj.get("geometri") or {}).get("wkt")
        if not wkt:
            continue
        kind, coords = parse_wkt(wkt)
        if kind != "POINT" or not coords or not coords[0]:
            continue
        lon, lat = coords[0][0]
        takst = egenskap(obj, "takst liten bil") or egenskap(obj, "takst")
        out.append({
            "id": f"nvdb-{obj['id']}",
            "name": egenskap(obj, "navn bomstasjon") or egenskap(obj, "navn") or "",
            "lat": lat,
            "lon": lon,
            "takst_nok": float(takst) if takst is not None else 0.0,
        })
    return out


def fetch_turistveger(base: str, type_id: int) -> dict:
    features = []
    for obj in fetch_all(base, type_id):
        wkt = (obj.get("geometri") or {}).get("wkt")
        if not wkt:
            continue
        kind, coords = parse_wkt(wkt)
        if kind == "LINESTRING":
            geometry = {"type": "LineString", "coordinates": coords[0]}
        elif kind == "MULTILINESTRING":
            geometry = {"type": "MultiLineString", "coordinates": coords}
        else:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "nvdb_id": obj["id"],
                "name": egenskap(obj, "navn") or "",
                "type": egenskap(obj, "turistvegtype") or "",
            },
            "geometry": geometry,
        })
    return {"type": "FeatureCollection", "features": features}


def main() -> int:
    last_err = None
    for base in BASES:
        try:
            print(f"Prøver {base} ...")
            ids = resolve_type_ids(base)

            tolls = fetch_toll_stations(base, ids["bomstasjon"])
            (DATA_DIR / "toll_stations.json").write_text(
                json.dumps(tolls, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  Skrev {len(tolls)} bomstasjoner -> data/toll_stations.json")

            tv = fetch_turistveger(base, ids["turistveg"])
            (DATA_DIR / "turistveger.geojson").write_text(
                json.dumps(tv, ensure_ascii=False), encoding="utf-8")
            print(f"  Skrev {len(tv['features'])} turistveg-strekninger -> data/turistveger.geojson")

            print("Ferdig. NB: ferry_crossings.json vedlikeholdes manuelt.")
            return 0
        except Exception as e:  # prøv neste base
            last_err = e
            print(f"  Feilet mot {base}: {type(e).__name__}: {e}")
    print(f"Alle NVDB-baser feilet. Siste feil: {last_err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
