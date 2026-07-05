"""Ende-til-ende-test av MVP-sløyfen med stub-providere.

Preferanser → 3 varianter → dagsplan → kostnader → redigering m/
regenerering → valg → evaluering.
"""
import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite://"  # in-memory

from app.db import engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# In-memory SQLite må dele connection på tvers av sesjoner:
import app.db as db_mod  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

db_mod.engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
db_mod.SessionLocal = sessionmaker(bind=db_mod.engine, autoflush=False)

import app.main as main_mod  # noqa: E402

main_mod.engine = db_mod.engine
from app.db import Base  # noqa: E402

Base.metadata.create_all(db_mod.engine)

client = TestClient(main_mod.app)

OSLO = {"name": "Oslo", "lat": 59.9139, "lon": 10.7522}
BERGEN = {"name": "Bergen", "lat": 60.3913, "lon": 5.3221}


@pytest.fixture()
def trip():
    r = client.post("/trips", json={
        "origin": OSLO, "destination": BERGEN, "start_date": "2026-08-01", "days": 3,
    })
    assert r.status_code == 201, r.text
    return r.json()


def variants_by_kind(trip_data):
    return {v["kind"]: v for v in trip_data["variants"]}


def test_three_distinct_variants(trip):
    v = variants_by_kind(trip)
    assert set(v) == {"fastest", "cheapest", "scenic"}
    assert v["fastest"]["total_drive_mins"] == min(
        x["total_drive_mins"] for x in v.values())
    assert v["cheapest"]["total_cost_nok"] == min(
        x["total_cost_nok"] for x in v.values())
    assert v["scenic"]["scenic_score"] == max(x["scenic_score"] for x in v.values())


def test_day_plan_and_costs(trip):
    v = variants_by_kind(trip)["fastest"]
    assert len(v["legs"]) == 3
    kinds = {c["kind"] for c in v["cost_items"]}
    assert "fuel" in kinds and "lodging" in kinds
    # Overnatting alle netter unntatt siste dag:
    lodging_items = [c for c in v["cost_items"] if c["kind"] == "lodging"]
    assert len(lodging_items) == 2
    # Kostnadssum er konsistent:
    assert sum(c["amount_nok"] for c in v["cost_items"]) == pytest.approx(
        v["total_cost_nok"], abs=1)


def test_max_drive_mins_forces_more_days():
    client.put("/me/preferences", json={"max_drive_mins_per_leg": 120})
    r = client.post("/trips", json={
        "origin": OSLO, "destination": BERGEN, "start_date": "2026-08-01", "days": 2,
    })
    v = variants_by_kind(r.json())["fastest"]
    for leg in v["legs"]:
        assert leg["drive_mins"] <= 120  # hard begrensning brytes aldri
    assert len(v["legs"]) > 2
    client.put("/me/preferences", json={"max_drive_mins_per_leg": 300})


def test_corridor_excludes_far_poi(trip):
    all_pois = {
        s["poi_id"]
        for v in trip["variants"] for l in v["legs"] for s in l["stops"]
    }
    assert "osm-trondheim-nidaros" not in all_pois  # negativ kontroll
    assert all_pois, "forventer stopp langs Oslo–Bergen"


def test_remove_stop_regenerates_without_poi(trip):
    v = variants_by_kind(trip)["scenic"]
    stop = next(s for l in v["legs"] for s in l["stops"])
    r = client.patch(f"/trips/{trip['id']}/stops/{stop['id']}",
                     json={"action": "remove"})
    assert r.status_code == 200
    data = r.json()
    assert stop["poi_id"] in data["excluded_poi_ids"]  # PREF-27
    remaining = {
        s["poi_id"] for v in data["variants"] for l in v["legs"] for s in l["stops"]
    }
    assert stop["poi_id"] not in remaining


def test_lock_stop_survives_regeneration(trip):
    v = variants_by_kind(trip)["fastest"]
    stop = next(s for l in v["legs"] for s in l["stops"])
    r = client.patch(f"/trips/{trip['id']}/stops/{stop['id']}", json={"action": "lock"})
    assert r.status_code == 200
    r = client.post(f"/trips/{trip['id']}/regenerate")
    fastest = variants_by_kind(r.json())["fastest"]
    locked = [s for l in fastest["legs"] for s in l["stops"] if s["locked"]]
    assert any(s["poi_id"] == stop["poi_id"] for s in locked)


def test_budget_flagging(trip):
    client.put("/me/preferences", json={"budget_total_nok": 100.0})
    r = client.get(f"/trips/{trip['id']}")
    flags = r.json()["budget_exceeded"]
    assert all(flags.values())  # 100 kr rekker ikke til Bergen
    client.put("/me/preferences", json={"budget_total_nok": None})


def test_choose_and_evaluate(trip):
    variant_id = trip["variants"][0]["id"]
    r = client.post(f"/trips/{trip['id']}/choose", json={"variant_id": variant_id})
    assert r.json()["status"] == "chosen"
    r = client.post(f"/trips/{trip['id']}/evaluation",
                    json={"rating": 5, "text": "Vøringsfossen!"})
    assert r.status_code == 201
    assert r.json()["status"] == "completed"  # DATA-01 lukker sløyfen
    # Dobbel evaluering avvises:
    r = client.post(f"/trips/{trip['id']}/evaluation", json={"rating": 1})
    assert r.status_code == 409


def test_poi_search():
    r = client.get("/pois/search", params={"q": "fløibanen"})
    assert [p["id"] for p in r.json()] == ["osm-floibanen"]
