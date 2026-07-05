"""PostGIS-basert PoiProvider (produksjon).

Korridorsøket fra mvp-spec kap. 5: ST_DWithin mot rutegeometrien, sortert
langs ruten med ST_LineLocatePoint. Velges med POI_PROVIDER=postgis.
Data importeres med backend/scripts/import_pois_osm.py.
"""
from __future__ import annotations

import json
import os

from .base import PoiRecord

_SELECT = """
SELECT id, name, lat, lon, category, subcategory, price_level, duration_mins,
       attributes, description,
       ST_LineLocatePoint(ST_GeomFromText(%(wkt)s, 4326), geog::geometry) AS pos
FROM pois
WHERE ST_DWithin(geog, ST_GeogFromText(%(wkt)s), %(buffer_m)s)
"""


def _record(row) -> PoiRecord:
    attributes = row[8]
    if isinstance(attributes, str):
        attributes = json.loads(attributes)
    return PoiRecord(
        id=row[0], name=row[1], lat=row[2], lon=row[3], category=row[4],
        subcategory=row[5], price_level=row[6], duration_mins=row[7],
        attributes=attributes or {}, description=row[9] or "",
        route_pos=float(row[10] or 0.0),
    )


class PostgisPoiProvider:
    def __init__(self, dsn: str | None = None):
        import psycopg  # importeres her så stub-oppsett ikke krever psycopg

        self._psycopg = psycopg
        self.dsn = dsn or os.environ.get(
            "POSTGIS_DSN", "postgresql://reiseliv:reiseliv-dev@localhost:5432/reiseliv"
        )

    def along_route(self, geometry, buffer_km, categories):
        wkt = "LINESTRING(" + ", ".join(f"{lon} {lat}" for lon, lat in geometry) + ")"
        sql = _SELECT
        params: dict = {"wkt": wkt, "buffer_m": buffer_km * 1000}
        if categories:
            sql += " AND category = ANY(%(categories)s)"
            params["categories"] = list(categories)
        sql += " ORDER BY pos"
        with self._psycopg.connect(self.dsn) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_record(r) for r in rows]

    def search(self, q: str) -> list[PoiRecord]:
        with self._psycopg.connect(self.dsn) as conn:
            rows = conn.execute(
                "SELECT id, name, lat, lon, category, subcategory, price_level,"
                " duration_mins, attributes, description, 0 FROM pois"
                " WHERE name ILIKE %s ORDER BY name LIMIT 25",
                (f"%{q}%",),
            ).fetchall()
        return [_record(r) for r in rows]
