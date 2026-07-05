"""Valhalla-basert RoutingProvider (produksjon).

Skjelett: kobler mot selvhostet Valhalla (se infra/docker-compose.yml).
Byttes inn for stub via miljøvariabelen ROUTING_PROVIDER=valhalla.

TODO før produksjon:
  - scenic_score: match rutegeometri mot Nasjonale turistveger-geometrien
    (NVDB) + viewpoint-tetthet fra POI-databasen (se spike/RESULTS.md #7).
  - toll/ferry: Valhalla gir use_tolls/use_ferry-kostnader, men kronebeløp
    hentes fra NVDB objekttype 45 og fergesjablonger.
"""
from __future__ import annotations

import json
import os
import urllib.request

from .base import RouteCandidate


class ValhallaRoutingProvider:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.environ.get("VALHALLA_URL", "http://localhost:8002")

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
            out.append(
                RouteCandidate(
                    name=f"valhalla-{i}",
                    geometry=_decode_polyline6(trip["legs"][0]["shape"]),
                    km=summary["length"],
                    drive_mins=int(summary["time"] / 60),
                    toll_nok=0.0,   # TODO: NVDB objekttype 45
                    ferry_nok=0.0,  # TODO: fergesjablong per samband
                    scenic_score=0.5,  # TODO: Nasjonale turistveger-match
                )
            )
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
