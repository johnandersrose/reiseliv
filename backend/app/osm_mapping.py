"""Mapping fra OSM-tags til Poi-skjemaet vårt (jf. mvp-spec kap. 2).

Ren logikk uten osmium/DB-avhengigheter, slik at reglene kan enhetstestes.
Brukes av backend/scripts/import_pois_osm.py.

Subkategoriene matcher interessene i Preferences (natur/kultur/sport/
gastronomi) slik at PREF-06-filteret virker rett på importerte data.
"""
from __future__ import annotations

# (tag-nøkkel, tag-verdi) → (category, subcategory, duration_mins)
# Rekkefølgen er prioritert: første treff vinner.
_RULES: list[tuple[str, str, tuple[str, str, int]]] = [
    # Overnatting
    ("tourism", "hotel", ("lodging", "hotel", 0)),
    ("tourism", "guest_house", ("lodging", "guest_house", 0)),
    ("tourism", "hostel", ("lodging", "hostel", 0)),
    ("tourism", "chalet", ("lodging", "cabin", 0)),
    ("tourism", "camp_site", ("lodging", "camping", 0)),
    ("tourism", "apartment", ("lodging", "apartment", 0)),
    # Mat
    ("amenity", "restaurant", ("food", "restaurant", 75)),
    ("amenity", "cafe", ("food", "cafe", 45)),
    ("amenity", "fast_food", ("food", "fast_food", 30)),
    ("amenity", "pub", ("food", "pub", 60)),
    # Aktiviteter og severdigheter
    ("tourism", "museum", ("activity", "kultur", 120)),
    ("tourism", "gallery", ("activity", "kultur", 90)),
    ("tourism", "theme_park", ("activity", "familie", 240)),
    ("tourism", "zoo", ("activity", "familie", 180)),
    ("tourism", "attraction", ("activity", "kultur", 90)),
    ("leisure", "sports_centre", ("activity", "sport", 120)),
    ("leisure", "water_park", ("activity", "familie", 180)),
    ("tourism", "viewpoint", ("sight", "natur", 30)),
    ("waterway", "waterfall", ("sight", "natur", 30)),
    ("tourism", "picnic_site", ("rest", "natur", 30)),
    ("highway", "rest_area", ("rest", "", 20)),
]

# OSM oppgir sjelden pris; sjablong per subkategori (1 billig .. 4 dyr).
_PRICE_LEVELS = {
    "hostel": 1, "camping": 1, "fast_food": 1, "rest": 1,
    "cafe": 2, "pub": 2, "guest_house": 2, "cabin": 2, "apartment": 2,
    "restaurant": 3, "hotel": 3,
}


def map_tags(tags: dict[str, str]) -> dict | None:
    """OSM-tags → Poi-felter, eller None hvis objektet ikke er en POI for oss.

    Objekter uten navn hoppes over: de kan ikke vises meningsfullt i en
    reiseplan (unntak: rasteplasser, som får generisk navn).
    """
    match = None
    for key, value, result in _RULES:
        if tags.get(key) == value:
            match = result
            break
    if match is None:
        return None

    category, subcategory, duration = match
    name = tags.get("name", "").strip()
    if not name:
        if category != "rest":
            return None
        name = "Rasteplass"

    attributes = {}
    if tags.get("wheelchair") == "yes":
        attributes["wheelchair"] = True
    if tags.get("dog") in ("yes", "leashed"):
        attributes["dogFriendly"] = True
    if tags.get("internet_access") in ("wlan", "yes"):
        attributes["wifi"] = True
    if category == "lodging" and tags.get("breakfast") == "yes":
        attributes["breakfastIncluded"] = True

    return {
        "name": name,
        "category": category,
        "subcategory": subcategory,
        "price_level": _PRICE_LEVELS.get(subcategory or category, 2),
        "duration_mins": duration,
        "attributes": attributes,
        "description": tags.get("description", ""),
    }
