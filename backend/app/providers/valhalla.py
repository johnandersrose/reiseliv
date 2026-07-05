"""Valhalla-basert RoutingProvider (produksjon).

Kobler mot selvhostet Valhalla (se infra/docker-compose.yml). Byttes inn for
stub via miljøvariabelen ROUTING_PROVIDER=valhalla.

Rutene berikes med bompenger (NVDB objekttype 45), fergesjablong og
scenic-score (Nasjonale turistveger-match) via RouteEnricher — kjør
backend/scripts/fetch_nvdb_data.py først for ekte data; ellers brukes
sample-filene og det logges en advarsel.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request

from ..enrichment import RouteEnricher
from .base import RouteCandidate

logger = logging.getLogger(__name__)


class ValhallaRoutingProvider:
    def __init__(self, base_url: str | None = None, enricher: RouteEnricher | None = None):
        self.base_url = base_url or os.environ.get("VALHALLA_URL", "http://localhost:8002")
        self.enricher = enricher or RouteEnricher()
        if self.enricher.uses_sample_data():
            logger.warning(
                "RouteEnricher bruker sample-data; kjør "
                "backend/scripts/fetch_nvdb_data.py for ekte NVDB-data."
            )

    def candidates(self, origin, destination, waypoints):
        body = {
            "locations": [
                {"lat": p["lat"], "lon": p["lon"]}
                for p in [origin, *waypoints, destination]
            ],
            "costing": "auto",
            "alternates": 2,
        }
        req = urllib.request.Request(
            f"{self.base_url}/route",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())

        out = []
        for i, trip in enumerate([data["trip"], *[a["trip"] for a in data.get("alternates", [])]]):
            summary = trip["summary"]
            candidate = RouteCandidate(
                name=f"valhalla-{i}",
                geometry=_decode_polyline6(trip["legs"][0]["shape"]),
                km=summary["length"],
                drive_mins=int(summary["time"] / 60),
                toll_nok=0.0,
                ferry_nok=0.0,
                scenic_score=0.0,
            )
            out.append(self.enricher.enrich(candidate))
        return out


def _decode_polyline6(shape: str) -> list[list[float]]:
    """Valhalla bruker polyline med presisjon 1e-6."""
    coords, index, lat, lon = [], 0, 0, 0
    while index < len(shape):
        for is_lon in (False, True):
            shift = result = 0
            while True:
                b = ord(shape[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if is_lon:
                lon += delta
            else:
                lat += delta
        coords.append([lon / 1e6, lat / 1e6])
    return coords
