"""Genererer de tre rutevariantene og dag-for-dag-planen.

Jf. docs/mvp-spec.md kap. 3: samme pipeline, tre målfunksjoner.
Konfliktregler (spec kap. 2): harde begrensninger (kjøretid per etappe,
dagstider) brytes aldri; budsjett flagges, men stopper ikke generering.

Dagsplanleggingen er geografisk: hvert stopp har en posisjon langs ruten
(PoiRecord.route_pos), stoppene legges i kjøreretning, og ankomsttidene
beregnes fra andelen av dagens kjøretid frem til stoppet. Stopp som ikke
rekkes innenfor dagens sluttid droppes. POI-er utenfor sesong for den
aktuelle reisedagen filtreres bort.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

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
    return f"{int(minutes) // 60:02d}:{int(minutes) % 60:02d}"


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


def _month_for_day(start_date: str, day_index: int) -> int:
    try:
        return (date.fromisoformat(start_date) + timedelta(days=day_index)).month
    except ValueError:
        return 7  # ugyldig dato: anta høysesong fremfor å feile


def _pick_day_stops(
    pool: list[PoiRecord], is_last_day: bool, used: set[str]
) -> list[tuple[PoiRecord, str]]:
    """Velg dagens stopp fra korridor-poolen: aktivitet, mat og overnatting."""
    picks: list[tuple[PoiRecord, str]] = []

    def take(categories: tuple[str, ...], stop_kind: str, key=None):
        options = [p for p in pool if p.category in categories and p.id not in used]
        if not options:
            return
        poi = max(options, key=key) if key else options[0]
        used.add(poi.id)
        picks.append((poi, stop_kind))

    take(("activity", "sight"), "activity")
    take(("food",), "food")
    if not is_last_day:
        # Overnatting nærmest dagens endepunkt, så neste dag starter riktig.
        take(("lodging",), "lodging", key=lambda p: p.route_pos)
    return picks


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

    day_start = _mins(prefs.day_start)
    day_end = _mins(prefs.day_end)
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

        # Dagens korridorsegment + sesongfilter for akkurat denne reisedagen.
        frac_lo, frac_hi = day / days, (day + 1) / days
        month = _month_for_day(trip.start_date, day)
        pool = [
            p for p in available
            if p.id not in used_ids
            and frac_lo <= p.route_pos < frac_hi
            and (not p.season_months or month in p.season_months)
        ]

        picks = _pick_day_stops(pool, is_last_day=(day == days - 1), used=used_ids)

        # Låste stopp (BRUK-12) gjeninnsettes med sin posisjon langs ruten.
        for ls in locked_here:
            if ls.day_index == day and ls.poi_id not in {p.id for p, _ in picks}:
                poi = by_id.get(ls.poi_id)
                if poi is None:
                    poi = PoiRecord(
                        id=ls.poi_id, name=ls.poi_id, lat=0, lon=0,
                        category=ls.kind, route_pos=frac_lo,
                    )
                used_ids.add(poi.id)
                picks.append((poi, ls.kind))

        # Geografisk skedulering: kjør, stopp, kjør videre — i kjøreretning.
        def rel(p: PoiRecord) -> float:
            return min(1.0, max(0.0, (p.route_pos - frac_lo) * days))

        clock = float(day_start)
        prev_rel = 0.0
        order = 0
        # Overnatting avslutter alltid dagen, uansett posisjon langs ruten.
        scheduled = sorted(picks, key=lambda t: (t[1] == "lodging", rel(t[0])))
        for poi, stop_kind in scheduled:
            arrival = clock + day_drive_mins * max(rel(poi) - prev_rel, 0.0)
            duration = poi.duration_mins or 60
            is_locked = any(
                ls.day_index == day and ls.poi_id == poi.id for ls in locked_here
            )
            if stop_kind != "lodging" and arrival + duration > day_end and not is_locked:
                continue  # rekkes ikke i dag – hard begrensning, hopp over
            departure = prefs.day_start if stop_kind == "lodging" else _hhmm(arrival + duration)
            db.add(
                models.Stop(
                    leg=leg, poi_id=poi.id, kind=stop_kind,
                    arrival=_hhmm(min(arrival, day_end)), departure=departure,
                    locked=is_locked, order=order,
                )
            )
            order += 1
            prev_rel = rel(poi)
            clock = arrival if stop_kind == "lodging" else arrival + duration
            if poi.category in ("activity", "sight"):
                cost = poi.price_level * ACTIVITY_NOK_PER_LEVEL * prefs.party_adults
                db.add(models.CostItem(
                    variant=variant, leg=leg, kind="activity", amount_nok=cost))
                total_cost += cost

        if day < days - 1:  # overnatting alle netter unntatt siste dag
            lodging_poi = next(
                (p for p, k in picks if k == "lodging"), None
            )
            night = LODGING_NIGHT_NOK.get(
                lodging_poi.price_level if lodging_poi else 2, 1200)
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
