#!/usr/bin/env python3
"""Importerer POI-er fra et OSM-ekstrakt (.osm.pbf/.osm) til PostGIS.

Bruk (lokalt, etter infra/setup.sh):

    pip install osmium "psycopg[binary]"
    python3 backend/scripts/import_pois_osm.py infra/valhalla_data/norway-latest.osm.pbf \
        --dsn postgresql://reiseliv:reiseliv-dev@localhost:5432/reiseliv

Tag-reglene bor i app/osm_mapping.py (enhetstestet). v1 importerer noder;
POI-er kartlagt som bygningsflater (ways/relations) kommer i v2 — for
reiselivskategoriene våre er nodedekningen i Norge god nok til å starte.
Lisens: OSM-data er ODbL — attribusjon kreves i frontend.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import osmium

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.osm_mapping import map_tags  # noqa: E402

DDL = """
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS pois (
    id            text PRIMARY KEY,
    name          text NOT NULL,
    lat           double precision NOT NULL,
    lon           double precision NOT NULL,
    category      text NOT NULL,
    subcategory   text NOT NULL DEFAULT '',
    price_level   int NOT NULL DEFAULT 2,
    duration_mins int NOT NULL DEFAULT 60,
    attributes    jsonb NOT NULL DEFAULT '{}',
    description   text NOT NULL DEFAULT '',
    source        text NOT NULL DEFAULT 'osm',
    geog          geography(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS pois_geog_idx ON pois USING gist (geog);
CREATE INDEX IF NOT EXISTS pois_category_idx ON pois (category);
"""

UPSERT = """
INSERT INTO pois (id, name, lat, lon, category, subcategory, price_level,
                  duration_mins, attributes, description, geog)
VALUES (%(id)s, %(name)s, %(lat)s, %(lon)s, %(category)s, %(subcategory)s,
        %(price_level)s, %(duration_mins)s, %(attributes)s, %(description)s,
        ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name, category = EXCLUDED.category,
    subcategory = EXCLUDED.subcategory, attributes = EXCLUDED.attributes,
    geog = EXCLUDED.geog;
"""


class PoiHandler(osmium.SimpleHandler):
    def __init__(self, sink):
        super().__init__()
        self.sink = sink
        self.count = 0

    def node(self, n):
        poi = map_tags(dict(n.tags))
        if poi is None or not n.location.valid():
            return
        poi.update(id=f"osm-n{n.id}", lat=n.location.lat, lon=n.location.lon)
        self.sink(poi)
        self.count += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("osm_file", help=".osm.pbf eller .osm")
    ap.add_argument("--dsn", default=os.environ.get(
        "POSTGIS_DSN", "postgresql://reiseliv:reiseliv-dev@localhost:5432/reiseliv"))
    ap.add_argument("--dry-run", action="store_true",
                    help="tell og vis eksempler uten å skrive til databasen")
    args = ap.parse_args()

    if args.dry_run:
        samples = []

        def sink(poi):
            if len(samples) < 10:
                samples.append(poi)

        handler = PoiHandler(sink)
        handler.apply_file(args.osm_file)
        for s in samples:
            print(f"  {s['category']:8} {s['name']}")
        print(f"Dry-run: {handler.count} POI-er ville blitt importert.")
        return 0

    import json

    import psycopg

    with psycopg.connect(args.dsn) as conn:
        conn.execute(DDL)
        batch = []

        def sink(poi):
            poi["attributes"] = json.dumps(poi["attributes"])
            batch.append(poi)
            if len(batch) >= 1000:
                conn.cursor().executemany(UPSERT, batch)
                batch.clear()

        handler = PoiHandler(sink)
        handler.apply_file(args.osm_file)
        if batch:
            conn.cursor().executemany(UPSERT, batch)
        conn.commit()
        print(f"Importerte {handler.count} POI-er til {args.dsn.split('@')[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
