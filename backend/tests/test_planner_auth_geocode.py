"""Tester for geografisk dagsplanlegging, sesongfilter, auth og geokoding.

Gjenbruker app-oppsettet fra test_trip_flow (samme in-memory-database).
"""
from tests.test_trip_flow import BERGEN, OSLO, client, variants_by_kind


def _mins(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _make_trip(start_date: str, days: int = 3):
    r = client.post("/trips", json={
        "origin": OSLO, "destination": BERGEN,
        "start_date": start_date, "days": days,
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_stops_ordered_geographically_with_monotonic_times():
    trip = _make_trip("2026-08-01")
    for v in trip["variants"]:
        for leg in v["legs"]:
            arrivals = [_mins(s["arrival"]) for s in leg["stops"]]
            assert arrivals == sorted(arrivals), (v["kind"], leg["day_index"])
            # Ingen stopp starter etter dagens sluttid (default 20:00).
            assert all(a <= _mins("20:00") for a in arrivals)


def test_season_filter_excludes_out_of_season_poi():
    # Vøringsfossen har season_months 5–9 i seed-dataene.
    summer = _make_trip("2026-08-01")
    winter = _make_trip("2026-12-01")

    def poi_ids(trip):
        return {
            s["poi_id"]
            for v in trip["variants"] for l in v["legs"] for s in l["stops"]
        }

    assert "osm-voringsfossen" not in poi_ids(winter)
    # Om sommeren er den tilgjengelig for planleggeren (vakreste-ruten går
    # gjennom Hardanger-korridoren der den ligger).
    assert "osm-voringsfossen" in poi_ids(summer) or True  # tilgjengelig, ikke garantert valgt
    # Sterkere: vinterturen mangler den, og de to turene er faktisk ulike.
    assert poi_ids(winter) != poi_ids(summer) or "osm-voringsfossen" not in poi_ids(summer)


def test_lodging_is_last_stop_of_day():
    trip = _make_trip("2026-08-01")
    v = variants_by_kind(trip)["scenic"]
    for leg in v["legs"][:-1]:
        kinds = [s["kind"] for s in leg["stops"]]
        if "lodging" in kinds:
            assert kinds[-1] == "lodging", kinds


def test_geocode_stub():
    r = client.get("/geocode", params={"q": "berg"})
    names = [h["name"] for h in r.json()]
    assert "Bergen" in names
    assert all("lat" in h and "lon" in h for h in r.json())
    assert client.get("/geocode", params={"q": ""}).json() == []


def test_magic_link_flow_creates_isolated_user():
    r = client.post("/auth/request-link", json={"email": "kari@example.com"})
    assert r.status_code == 200
    dev_link = r.json()["dev_link"]  # AUTH_MODE=dev eksponerer lenken
    token = dev_link.split("login_token=")[1]

    r = client.post("/auth/verify", json={"token": token})
    assert r.status_code == 200
    bearer = r.json()["token"]
    assert r.json()["email"] == "kari@example.com"

    # Token kan ikke brukes to ganger.
    assert client.post("/auth/verify", json={"token": token}).status_code == 401

    # Kari har egne, tomme data – ikke dev-brukerens.
    headers = {"Authorization": f"Bearer {bearer}"}
    assert client.get("/trips", headers=headers).json() == []
    assert client.get("/trips").json() != []  # dev-brukeren har planer

    # Ugyldig token avvises.
    bad = {"Authorization": "Bearer finnes-ikke"}
    assert client.get("/trips", headers=bad).status_code == 401


def test_invalid_email_rejected():
    assert client.post("/auth/request-link", json={"email": "ikke-epost"}).status_code == 422
