"""Geokoding: stedsnavn → koordinater (BRUK-16, vilkårlige destinasjoner).

Produksjon: Kartverkets åpne stedsnavn-API (ws.geonorge.no, gratis, ingen
nøkkel). Velges med GEOCODER=kartverket. Dev/test: StubGeocoder med de
vanligste byene, så frontend og tester virker uten nett.

NB: Kartverket-kallet er skrevet mot dokumentert API-format, men må
valideres ved første kjøring med nettilgang (sandkassen når ikke geonorge).
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Protocol


@dataclass
class GeocodeHit:
    name: str
    lat: float
    lon: float
    municipality: str = ""


class Geocoder(Protocol):
    def search(self, q: str, limit: int = 8) -> list[GeocodeHit]: ...


_STUB_PLACES = [
    ("Oslo", 59.9139, 10.7522, "Oslo"),
    ("Bergen", 60.3913, 5.3221, "Bergen"),
    ("Trondheim", 63.4305, 10.3951, "Trondheim"),
    ("Stavanger", 58.9690, 5.7331, "Stavanger"),
    ("Kristiansand", 58.1467, 7.9956, "Kristiansand"),
    ("Tromsø", 69.6492, 18.9553, "Tromsø"),
    ("Ålesund", 62.4722, 6.1549, "Ålesund"),
    ("Bodø", 67.2804, 14.4049, "Bodø"),
    ("Lillehammer", 61.1153, 10.4662, "Lillehammer"),
    ("Geilo", 60.5336, 8.2049, "Hol"),
    ("Eidfjord", 60.4665, 7.0716, "Eidfjord"),
    ("Voss", 60.6300, 6.4410, "Voss"),
    ("Flåm", 60.8630, 7.1130, "Aurland"),
    ("Røros", 62.5747, 11.3842, "Røros"),
    ("Lofoten (Svolvær)", 68.2343, 14.5684, "Vågan"),
]


class StubGeocoder:
    def search(self, q: str, limit: int = 8) -> list[GeocodeHit]:
        ql = q.strip().lower()
        if not ql:
            return []
        hits = [
            GeocodeHit(name=n, lat=lat, lon=lon, municipality=k)
            for n, lat, lon, k in _STUB_PLACES
            if ql in n.lower()
        ]
        return hits[:limit]


class KartverketGeocoder:
    BASE = "https://ws.geonorge.no/stedsnavn/v1/navn"

    def search(self, q: str, limit: int = 8) -> list[GeocodeHit]:
        if not q.strip():
            return []
        params = urllib.parse.urlencode({
            "sok": f"{q.strip()}*",
            "fuzzy": "true",
            "utkoordsys": 4258,  # ETRS89 ≈ WGS84 lengde/bredde
            "treffPerSide": limit,
            "side": 1,
        })
        req = urllib.request.Request(
            f"{self.BASE}?{params}",
            headers={"Accept": "application/json",
                     "User-Agent": "reiseliv/0.1 (kontakt: se repo)"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        out = []
        for navn in data.get("navn", []):
            punkt = navn.get("representasjonspunkt") or {}
            if "nord" not in punkt or "øst" not in punkt:
                continue
            kommuner = navn.get("kommuner") or []
            out.append(GeocodeHit(
                name=navn.get("skrivemåte", ""),
                lat=punkt["nord"],
                lon=punkt["øst"],
                municipality=kommuner[0].get("kommunenavn", "") if kommuner else "",
            ))
        return out
