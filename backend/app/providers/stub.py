"""Stub-providere for utvikling og test.

Ruter syntetiseres fra luftlinje × veifaktor med tre profiler som gir reelt
ulike raskeste/billigste/vakreste-valg. POI-er leses fra seed_pois.json og
plasseres i korridor med haversine-avstand til rutelinjen.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .base import PoiRecord, RouteCandidate

EARTH_KM = 6371.0


def haversine_km(a: list[float], b: list[float]) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def _interpolate(a: list[float], b: list[float], n: int, bulge: float) -> list[list[float]]:
    """Rett linje a→b med `n` punkter og en liten sideveis bue (skiller profilene)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        lon = a[0] + (b[0] - a[0]) * t
        lat = a[1] + (b[1] - a[1]) * t + bulge * math.sin(math.pi * t)
        pts.append([round(lon, 5), round(lat, 5)])
    return pts


# (navn, veifaktor, snittfart km/t, scenic, bom kr/km, ferge kr, bue)
_PROFILES = [
    ("hovedvei", 1.25, 75.0, 0.40, 0.35, 0.0, 0.0),
    ("lavkost", 1.35, 65.0, 0.50, 0.05, 0.0, -0.15),
    ("turistveg", 1.45, 58.0, 0.90, 0.15, 200.0, 0.15),
]


class StubRoutingProvider:
    def candidates(self, origin, destination, waypoints):
        via = [origin, *waypoints, destination]
        air_km = sum(
            haversine_km([p["lon"], p["lat"]], [q["lon"], q["lat"]])
            for p, q in zip(via, via[1:])
        )
        out = []
        for name, factor, speed, scenic, toll_per_km, ferry, bulge in _PROFILES:
            km = air_km * factor
            geometry = []
            for p, q in zip(via, via[1:]):
                seg = _interpolate([p["lon"], p["lat"]], [q["lon"], q["lat"]], 20, bulge)
                geometry.extend(seg if not geometry else seg[1:])
            out.append(
                RouteCandidate(
                    name=name,
                    geometry=geometry,
                    km=round(km, 1),
                    drive_mins=int(km / speed * 60),
                    toll_nok=round(km * toll_per_km, 0),
                    ferry_nok=ferry,
                    scenic_score=scenic,
                )
            )
        return out


class StubPoiProvider:
    def __init__(self, seed_path: Path | None = None):
        path = seed_path or Path(__file__).with_name("seed_pois.json")
        self._pois = [PoiRecord(**p) for p in json.loads(path.read_text(encoding="utf-8"))]

    def along_route(self, geometry, buffer_km, categories):
        hits = []
        for poi in self._pois:
            if categories and poi.category not in categories:
                continue
            best_i, best_d = None, float("inf")
            for i, pt in enumerate(geometry):
                d = haversine_km([poi.lon, poi.lat], pt)
                if d < best_d:
                    best_i, best_d = i, d
            if best_d <= buffer_km:
                hits.append((best_i, poi))
        hits.sort(key=lambda t: t[0])
        return [p for _, p in hits]
