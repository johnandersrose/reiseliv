"""Ruteberikelse: bompenger, ferge og scenic-score fra åpne datakilder.

Fyller TODO-ene i ValhallaRoutingProvider (jf. spike/RESULTS.md #2, #4, #7):

  - toll_nok:     sum av takster for bomstasjoner (NVDB objekttype 45) som
                  ligger på ruten (< TOLL_HIT_KM fra rutelinjen)
  - ferry_nok:    sjablongtakst for fergesamband ruten krysser
  - scenic_score: andel av ruten som følger Nasjonale turistveger
                  + tetthet av utsiktspunkter i korridoren

Datafiler i backend/data/ produseres av backend/scripts/fetch_nvdb_data.py
(kjøres lokalt — krever nettilgang). Uten ekte filer brukes *.sample.*-filene,
som er grove tilnærminger kun til utvikling og test.
"""
from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

from .providers.base import RouteCandidate

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TOLL_HIT_KM = 0.5      # bomstasjon regnes som passert innenfor denne avstanden
FERRY_HIT_KM = 3.0     # fergesamband regnes som brukt innenfor denne avstanden
SCENIC_BUFFER_KM = 3.0  # rutepunkt regnes som «på turistveg» innenfor denne

KM_PER_DEG = 111.32


def _project(pt: list[float], ref_lat_rad: float) -> tuple[float, float]:
    """Ekvirektangulær projeksjon [lon, lat] → (x, y) i km. God nok lokalt."""
    return pt[0] * math.cos(ref_lat_rad) * KM_PER_DEG, pt[1] * KM_PER_DEG


def _point_segment_km(p, a, b, ref_lat_rad) -> float:
    px, py = _project(p, ref_lat_rad)
    ax, ay = _project(a, ref_lat_rad)
    bx, by = _project(b, ref_lat_rad)
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def min_distance_km(pt: list[float], line: list[list[float]]) -> float:
    """Minste avstand fra punkt [lon, lat] til en polyline, i km."""
    ref = math.radians(pt[1])
    if len(line) == 1:
        return _point_segment_km(pt, line[0], line[0], ref)
    return min(
        _point_segment_km(pt, a, b, ref) for a, b in zip(line, line[1:])
    )


def _load(path_real: Path, path_sample: Path):
    for p in (path_real, path_sample):
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")), p.name
    return None, None


class RouteEnricher:
    def __init__(self, data_dir: Path | None = None):
        d = data_dir or DATA_DIR
        self.toll_stations, self._toll_src = _load(
            d / "toll_stations.json", d / "toll_stations.sample.json")
        self.ferries, self._ferry_src = _load(
            d / "ferry_crossings.json", d / "ferry_crossings.sample.json")
        turistveger, self._turist_src = _load(
            d / "turistveger.geojson", d / "turistveger.sample.geojson")
        self.turistveg_lines: list[list[list[float]]] = []
        if turistveger:
            for feature in turistveger.get("features", []):
                geom = feature.get("geometry", {})
                if geom.get("type") == "LineString":
                    self.turistveg_lines.append(geom["coordinates"])
                elif geom.get("type") == "MultiLineString":
                    self.turistveg_lines.extend(geom["coordinates"])

    def uses_sample_data(self) -> bool:
        return any(
            src and ".sample." in src
            for src in (self._toll_src, self._ferry_src, self._turist_src)
        )

    # -- delberegninger ----------------------------------------------------

    def toll_nok(self, geometry: list[list[float]]) -> float:
        total = 0.0
        for st in self.toll_stations or []:
            pt = [st["lon"], st["lat"]]
            if min_distance_km(pt, geometry) <= TOLL_HIT_KM:
                total += st.get("takst_nok", 0.0)
        return round(total, 0)

    def ferry_nok(self, geometry: list[list[float]]) -> float:
        total = 0.0
        for f in self.ferries or []:
            pt = [f["lon"], f["lat"]]
            if min_distance_km(pt, geometry) <= FERRY_HIT_KM:
                total += f.get("takst_nok", 0.0)
        return round(total, 0)

    def scenic_overlap(self, geometry: list[list[float]]) -> float:
        """Andel av rutepunktene som ligger på/nær en nasjonal turistveg."""
        if not self.turistveg_lines or not geometry:
            return 0.0
        hits = sum(
            1
            for pt in geometry
            if any(
                min_distance_km(pt, line) <= SCENIC_BUFFER_KM
                for line in self.turistveg_lines
            )
        )
        return hits / len(geometry)

    def scenic_score(
        self, geometry: list[list[float]], km: float, viewpoints: int = 0
    ) -> float:
        """Jf. mvp-spec kap. 3: turistveg-andel + viewpoint-tetthet, 0..1."""
        overlap = self.scenic_overlap(geometry)
        per_100km = viewpoints / max(km / 100.0, 0.1)
        density = min(1.0, per_100km / 4.0)  # 4 utsiktspunkter/100 km ≈ maks
        return round(min(1.0, 0.15 + 0.60 * overlap + 0.25 * density), 2)

    # -- hovedinngang -------------------------------------------------------

    def enrich(self, candidate: RouteCandidate, viewpoints: int = 0) -> RouteCandidate:
        return replace(
            candidate,
            toll_nok=self.toll_nok(candidate.geometry),
            ferry_nok=self.ferry_nok(candidate.geometry),
            scenic_score=self.scenic_score(
                candidate.geometry, candidate.km, viewpoints
            ),
        )
