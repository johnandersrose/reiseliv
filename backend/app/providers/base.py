"""Provider-grensesnitt.

All geografi (rutemotor, korridorsøk) bor bak disse grensesnittene, slik at
stub-implementasjonen kan byttes til Valhalla/PostGIS uten å røre generatoren.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RouteCandidate:
    name: str
    geometry: list[list[float]]  # [[lon, lat], ...]
    km: float
    drive_mins: int
    toll_nok: float
    ferry_nok: float
    scenic_score: float  # 0..1


@dataclass
class PoiRecord:
    id: str
    name: str
    lat: float
    lon: float
    category: str  # activity|food|lodging|sight|rest
    subcategory: str = ""
    price_level: int = 2  # 1 (billig) .. 4 (dyr)
    duration_mins: int = 60
    season_months: list[int] = field(default_factory=lambda: list(range(1, 13)))
    attributes: dict = field(default_factory=dict)
    description: str = ""
    # Settes av PoiProvider.along_route: posisjon langs ruten, 0.0 (start)
    # til 1.0 (mål). Brukes av dagsplanleggeren til geografisk riktig
    # rekkefølge og tidsestimat for stoppene.
    route_pos: float = 0.0


class RoutingProvider(Protocol):
    def candidates(
        self, origin: dict, destination: dict, waypoints: list[dict]
    ) -> list[RouteCandidate]:
        """Alternative kjøreruter origin→destination (via waypoints)."""
        ...


class PoiProvider(Protocol):
    def along_route(
        self, geometry: list[list[float]], buffer_km: float, categories: list[str]
    ) -> list[PoiRecord]:
        """POI-er i en korridor rundt rutegeometrien, sortert langs ruten."""
        ...
