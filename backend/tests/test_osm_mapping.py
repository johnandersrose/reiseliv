"""Tester tag-mappingreglene og import-handleren mot en liten OSM-fixture."""
from pathlib import Path

from app.osm_mapping import map_tags

FIXTURE = Path(__file__).parent / "fixtures" / "sample.osm"


def test_hotel_mapping():
    poi = map_tags({"tourism": "hotel", "name": "Fjellhotellet", "breakfast": "yes"})
    assert poi["category"] == "lodging"
    assert poi["subcategory"] == "hotel"
    assert poi["price_level"] == 3
    assert poi["attributes"]["breakfastIncluded"] is True


def test_viewpoint_maps_to_natur_sight():
    poi = map_tags({"tourism": "viewpoint", "name": "Utsikten"})
    assert (poi["category"], poi["subcategory"]) == ("sight", "natur")


def test_accessibility_attributes():
    poi = map_tags({
        "amenity": "cafe", "name": "Kafeen", "wheelchair": "yes", "dog": "leashed",
    })
    assert poi["attributes"] == {"wheelchair": True, "dogFriendly": True}


def test_nameless_poi_skipped_except_rest_area():
    assert map_tags({"tourism": "hotel"}) is None
    rest = map_tags({"highway": "rest_area"})
    assert rest["name"] == "Rasteplass"


def test_irrelevant_tags_skipped():
    assert map_tags({"highway": "traffic_signals"}) is None
    assert map_tags({"shop": "supermarket", "name": "Butikken"}) is None


def test_import_handler_on_osm_fixture():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from import_pois_osm import PoiHandler

    collected = []
    handler = PoiHandler(collected.append)
    handler.apply_file(str(FIXTURE))

    assert handler.count == 3  # hotellet, utsikten, kafeen – ikke lyskrysset
    by_cat = {p["category"] for p in collected}
    assert by_cat == {"lodging", "sight", "food"}
    assert all(p["id"].startswith("osm-n") for p in collected)
    assert all("lat" in p and "lon" in p for p in collected)
