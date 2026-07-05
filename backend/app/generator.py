"""Genererer de tre rutevariantene og dag-for-dag-planen.

Jf. docs/mvp-spec.md kap. 3: samme pipeline, tre målfunksjoner.
Konfliktregler (spec kap. 2): harde begrensninger brytes aldri; budsjett
flagges, men stopper ikke generering.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from . import models
from .providers.base import PoiProvider, PoiRecord, RouteCandidate, RoutingProvider

# SSB tabell 09654, månedssnitt 2026M05 (live-verifisert i spike/RESULTS.md).
# Oppdateres av batchjobb i produksjon.
FUEL_NOK_PER_L = {"petrol": 19.15, "diesel": 20.02}
EV_NOK_PER_KWH = 5.0  # offentlig hurtiglading, sjablong
DEFAULT_L_PER_100KM = 6.5
DEFAULT_KWH_PER_100KM = 18.0

LODGING_NIGHT_NOK = {1: 700, 2: 1200, 3: 1900, 4: 3000}  # per price_level
ACTIVITY_NOK_PER_LEVEL = 125  # per voksen, sjablong

CORRIDOR_BUFFER_KM = 50.0

#             (w_tid, w_kost, w_scenic)
WEIGHTS = {
    "fastest": (1.0, 0.0, 0.0),
    "cheapest": (0.0, 1.0, 0.0),
    "scenic": (0.3, 0.0, 0.7),
}


@dataclass
class LockedStop:
    variant_kind: str
    day_index: int
    poi_id: str
    kind: str


def fuel_cost(km: float, vehicle: dict) -> float:
    vtype = (vehicle or {}).get("type", "petrol")
    if vtype == "ev":
        kwh = km / 100 * (vehicle.get("consumption_per_100km") or DEFAULT_KWH_PER_100KM)
        return round(kwh * EV_NOK_PER_KWH, 0)
    liters = km / 100 * ((vehicle or {}).get("consumption_per_100km") or DEFAULT_L_PER_100KM)
    return round(liters * FUEL_NOK_PER_L.get(vtype, FUEL_NOK_PER_L["petrol"]), 0)


def _variant_road_cost(c: RouteCandidate, vehicle: dict) -> float:
    return fuel_cost(c.km, vehicle) + c.toll_nok + c.ferry_nok


def pick_candidates(
    candidates: list[RouteCandidate], vehicle: dict
) -> dict[str, RouteCandidate]:
    """Velg vinnerkandidat per variant med normalisert vektet kostfunksjon."""
    max_mins = max(c.drive_mins for c in candidates) or 1
    costs = {id(c): _variant_road_cost(c, vehicle) for c in candidates}
    max_cost = max(costs.values()) or 1

    chosen = {}
    for kind, (wt, wc, ws) in WEIGHTS.items():
        chosen[kind] = min(
            candidates,
            key=lambda c: (
                wt * c.drive_mins / max_mins
                + wc * costs[id(c)] / max_cost
                + ws * (1 - c.scenic_score)
            ),
        )
    return chosen


def _hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _mins(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _split_geometry(geometry: list, parts: int) -> list[list]:
    """Del rutegeometrien i `parts` sammenhengende dagsetapper."""
    n = len(geometry)
    out = []
    for i in range(parts):
        a = round(i * (n - 1) / parts)
        b = round((i + 1) * (n - 1) / parts)
        out.append(geometry[a : b + 1])
    return out


def build_variant(
    db: Session,
    trip: models.TripPlan,
    prefs: models.Preferences,
    kind: str,
    candidate: RouteCandidate,
    pois: PoiProvider,
    locked: list[LockedStop],
) -> models.RouteVariant:
    vehicle = prefs.vehicle or {}
    interests = prefs.interests or []
    excluded = set(trip.excluded_poi_ids or [])

    # Harde begrensninger: maks kjøretid per etappe kan tvinge flere dager.
    days = max(trip.days, math.ceil(candidate.drive_mins / prefs.max_drive_mins_per_leg))
    day_geoms = _split_geometry(candidate.geometry, days)
    day_km = candidate.km / days
    day_drive_mins = candidate.drive_mins // days

    corridor = pois.along_route(candidate.geometry, CORRIDOR_BUFFER_KM, [])
    # Interessefilter for aktiviteter (PREF-06); øvrige kategorier beholdes.
    def _matches_interests(p: PoiRecord) -> bool:
        if p.category not in ("activity", "sight") or not interests:
            return True
        return not p.subcategory or p.subcategory in interests

    available = [p for p in corridor if p.id not in excluded and _matches_interests(p)]
    per_day = _split_geometry([p.id for p in available], days) if available else [[]] * days
    by_id = {p.id: p for p in available}
    locked_here = [ls for ls in locked if ls.variant_kind == kind]

    variant = models.RouteVariant(
        trip_plan=trip,
        kind=kind,
        total_km=candidate.km,
        total_drive_mins=candidate.drive_mins,
        total_cost_nok=0,
        scenic_score=candidate.scenic_score,
    )
    db.add(variant)

    total_cost = candidate.toll_nok + candidate.ferry_nok
    if candidate.toll_nok:
        db.add(models.CostItem(variant=variant, kind="toll", amount_nok=candidate.toll_nok))
    if candidate.ferry_nok:
        db.add(models.CostItem(variant=variant, kind="ferry", amount_nok=candidate.ferry_nok))

    used_ids: set[str] = set()
    for day in range(days):
        leg = models.Leg(
            variant=variant,
            day_index=day,
            geometry=day_geoms[day],
            drive_mins=day_drive_mins,
            km=round(day_km, 1),
        )
        db.add(leg)
        leg_fuel = fuel_cost(day_km, vehicle)
        db.add(models.CostItem(variant=variant, leg=leg, kind="fuel", amount_nok=leg_fuel))
        total_cost += leg_fuel

        day_pool = [by_id[i] for i in per_day[day] if i in by_id and i not in used_ids]

        def take(category: str, fallback: str | None = None) -> PoiRecord | None:
            for pool_cat in filter(None, [category, fallback]):
                for p in day_pool:
                    if p.category == pool_cat and p.id not in used_ids:
                        used_ids.add(p.id)
                        return p
            return None

        clock = _mins(prefs.day_start)
        order = 0
        day_end = _mins(prefs.day_end)

        # Låste stopp (BRUK-12/PREF-22-forløper) legges inn først.
        for ls in [l for l in locked_here if l.day_index == day]:
            db.add(
                models.Stop(
                    leg=leg, poi_id=ls.poi_id, kind=ls.kind,
                    arrival=_hhmm(clock), departure=_hhmm(clock + 60),
                    locked=True, order=order,
                )
            )
            used_ids.add(ls.poi_id)
            clock += 60
            order += 1

        half_drive = day_drive_mins // 2
        clock += half_drive  # formiddagskjøring

        for slot_kind, category, fallback in (
            ("activity", "activity", "sight"),
            ("food", "food", None),
        ):
            poi = take(category, fallback)
            if poi and clock + poi.duration_mins <= day_end:
                db.add(
                    models.Stop(
                        leg=leg, poi_id=poi.id, kind=slot_kind,
                        arrival=_hhmm(clock), departure=_hhmm(clock + poi.duration_mins),
                        locked=False, order=order,
                    )
                )
                clock += poi.duration_mins
                order += 1
                if poi.category in ("activity", "sight"):
                    cost = poi.price_level * ACTIVITY_NOK_PER_LEVEL * prefs.party_adults
                    db.add(models.CostItem(
                        variant=variant, leg=leg, kind="activity", amount_nok=cost))
                    total_cost += cost

        clock = min(clock + (day_drive_mins - half_drive), day_end)  # ettermiddagskjøring

        if day < days - 1:  # overnatting alle netter unntatt siste dag
            lodging = take("lodging")
            night = LODGING_NIGHT_NOK.get(lodging.price_level if lodging else 2, 1200)
            if lodging:
                db.add(
                    models.Stop(
                        leg=leg, poi_id=lodging.id, kind="lodging",
                        arrival=_hhmm(clock), departure=prefs.day_start,
                        locked=False, order=order,
                    )
                )
            db.add(models.CostItem(variant=variant, leg=leg, kind="lodging", amount_nok=night))
            total_cost += night

    variant.total_cost_nok = round(total_cost, 0)
    return variant


def collect_locked(trip: models.TripPlan) -> list[LockedStop]:
    out = []
    for variant in trip.variants:
        for leg in variant.legs:
            for stop in leg.stops:
                if stop.locked:
                    out.append(LockedStop(variant.kind, leg.day_index, stop.poi_id, stop.kind))
    return out


def generate(
    db: Session,
    trip: models.TripPlan,
    prefs: models.Preferences,
    routing: RoutingProvider,
    pois: PoiProvider,
) -> None:
    """(Re)generer alle tre variantene. Låste stopp og fravalg bevares."""
    locked = collect_locked(trip)
    for old in list(trip.variants):
        db.delete(old)
    db.flush()

    candidates = routing.candidates(trip.origin, trip.destination, trip.waypoints or [])
    for kind, candidate in pick_candidates(candidates, prefs.vehicle or {}).items():
        build_variant(db, trip, prefs, kind, candidate, pois, locked)
    db.flush()
