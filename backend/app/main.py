"""REST-API – jf. docs/mvp-spec.md kap. 4.

Providere velges med miljøvariabler: ROUTING_PROVIDER=stub|valhalla,
POI_PROVIDER=stub|postgis, GEOCODER=stub|kartverket.

Auth: magic link (POST /auth/request-link → e-post med lenke →
POST /auth/verify → Bearer-token). I AUTH_MODE=dev (default) faller kall
uten token tilbake til en delt dev-bruker, og lenken logges i stedet for å
sendes — sett AUTH_MODE=required + en ekte EmailSender i produksjon.
"""
from __future__ import annotations

import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import generator, models
from .db import Base, engine, get_db
from .models import utcnow
from .providers.geocoder import KartverketGeocoder, StubGeocoder
from .providers.stub import StubPoiProvider, StubRoutingProvider
from .providers.valhalla import ValhallaRoutingProvider

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Reiseliv API", version="0.1.0", lifespan=lifespan)


def get_routing():
    if os.environ.get("ROUTING_PROVIDER", "stub") == "valhalla":
        return ValhallaRoutingProvider()
    return StubRoutingProvider()


def _make_poi_provider():
    if os.environ.get("POI_PROVIDER", "stub") == "postgis":
        from .providers.postgis import PostgisPoiProvider

        return PostgisPoiProvider()
    return StubPoiProvider()


_poi_provider = _make_poi_provider()


def get_pois():
    return _poi_provider


def get_geocoder():
    if os.environ.get("GEOCODER", "stub") == "kartverket":
        return KartverketGeocoder()
    return StubGeocoder()


# ---------- Auth ----------

class EmailSender:
    """Byttes til ekte leverandør (f.eks. Resend/Postmark) i produksjon."""

    def send_login_link(self, email: str, link: str) -> None:
        logger.info("Magic link til %s: %s", email, link)


_email_sender = EmailSender()


def _get_or_create_user(db: Session, email: str) -> models.User:
    user = db.scalar(select(models.User).where(models.User.email == email))
    if not user:
        user = models.User(email=email)
        user.preferences = models.Preferences(vehicle={"type": "petrol"})
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> models.User:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        session = db.scalar(
            select(models.ApiSession).where(models.ApiSession.token == token))
        if not session:
            raise HTTPException(401, "Ugyldig eller utløpt token")
        return db.get(models.User, session.user_id)
    if os.environ.get("AUTH_MODE", "dev") == "dev":
        return _get_or_create_user(db, "dev@reiseliv.local")
    raise HTTPException(401, "Innlogging kreves")


# ---------- Inn-skjemaer ----------

class Place(BaseModel):
    name: str
    lat: float
    lon: float


class TripCreate(BaseModel):
    name: str = ""
    origin: Place
    destination: Place
    waypoints: list[Place] = []
    start_date: str
    days: int = Field(ge=1, le=30)


class StopAction(BaseModel):
    action: str  # lock|unlock|remove


class ChooseVariant(BaseModel):
    variant_id: int


class EvaluationIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = ""


class PreferencesIn(BaseModel):
    party_adults: int = 2
    party_children_ages: list[int] = []
    dog: bool = False
    vehicle: dict = {"type": "petrol"}
    interests: list[str] = []
    budget_total_nok: float | None = None
    max_drive_mins_per_leg: int = 300
    day_start: str = "09:00"
    day_end: str = "20:00"
    lodging_types: list[str] = []


# ---------- Serialisering ----------

def stop_json(s: models.Stop) -> dict:
    return {"id": s.id, "poi_id": s.poi_id, "kind": s.kind, "arrival": s.arrival,
            "departure": s.departure, "locked": s.locked, "order": s.order}


def variant_json(v: models.RouteVariant) -> dict:
    return {
        "id": v.id,
        "kind": v.kind,
        "total_km": v.total_km,
        "total_drive_mins": v.total_drive_mins,
        "total_cost_nok": v.total_cost_nok,
        "scenic_score": v.scenic_score,
        "legs": [
            {"day_index": l.day_index, "km": l.km, "drive_mins": l.drive_mins,
             "geometry": l.geometry, "stops": [stop_json(s) for s in l.stops]}
            for l in v.legs
        ],
        "cost_items": [
            {"kind": c.kind, "amount_nok": c.amount_nok, "is_estimate": c.is_estimate}
            for c in v.cost_items
        ],
    }


def trip_json(t: models.TripPlan, budget: float | None = None) -> dict:
    out = {
        "id": t.id, "name": t.name, "origin": t.origin, "destination": t.destination,
        "start_date": t.start_date, "days": t.days, "status": t.status,
        "chosen_variant_id": t.chosen_variant_id,
        "excluded_poi_ids": t.excluded_poi_ids,
        "variants": [variant_json(v) for v in t.variants],
    }
    if budget is not None:
        # Konfliktregel 3 (spec kap. 2): budsjettbrudd flagges, stopper ikke.
        out["budget_exceeded"] = {
            v.kind: v.total_cost_nok > budget for v in t.variants
        }
    return out


def _get_trip(db: Session, user: models.User, trip_id: int) -> models.TripPlan:
    trip = db.get(models.TripPlan, trip_id)
    if not trip or trip.user_id != user.id:
        raise HTTPException(404, "Ukjent reiseplan")
    return trip


# ---------- Endepunkter ----------

@app.post("/trips", status_code=201)
def create_trip(
    body: TripCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    routing=Depends(get_routing),
    pois=Depends(get_pois),
):
    trip = models.TripPlan(
        user_id=user.id,
        name=body.name or f"{body.origin.name} – {body.destination.name}",
        origin=body.origin.model_dump(),
        destination=body.destination.model_dump(),
        waypoints=[w.model_dump() for w in body.waypoints],
        start_date=body.start_date,
        days=body.days,
    )
    db.add(trip)
    db.flush()
    generator.generate(db, trip, user.preferences, routing, pois)
    db.commit()
    db.refresh(trip)
    return trip_json(trip, user.preferences.budget_total_nok)


@app.get("/trips")
def list_trips(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    trips = db.scalars(select(models.TripPlan).where(models.TripPlan.user_id == user.id)).all()
    return [
        {"id": t.id, "name": t.name, "status": t.status, "days": t.days,
         "start_date": t.start_date}
        for t in trips
    ]


@app.get("/trips/{trip_id}")
def get_trip(trip_id: int, db: Session = Depends(get_db),
             user: models.User = Depends(get_current_user)):
    return trip_json(_get_trip(db, user, trip_id), user.preferences.budget_total_nok)


@app.patch("/trips/{trip_id}/stops/{stop_id}")
def patch_stop(
    trip_id: int,
    stop_id: int,
    body: StopAction,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    routing=Depends(get_routing),
    pois=Depends(get_pois),
):
    trip = _get_trip(db, user, trip_id)
    stop = db.get(models.Stop, stop_id)
    if not stop or stop.leg.variant.trip_plan_id != trip.id:
        raise HTTPException(404, "Ukjent stopp")

    if body.action == "lock":
        stop.locked = True
    elif body.action == "unlock":
        stop.locked = False
    elif body.action == "remove":
        # PREF-27: fravalg huskes og ekskluderes ved regenerering (BRUK-01).
        trip.excluded_poi_ids = [*(trip.excluded_poi_ids or []), stop.poi_id]
        generator.generate(db, trip, user.preferences, routing, pois)
    else:
        raise HTTPException(422, f"Ukjent handling: {body.action}")
    db.commit()
    db.refresh(trip)
    return trip_json(trip, user.preferences.budget_total_nok)


@app.post("/trips/{trip_id}/regenerate")
def regenerate(
    trip_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    routing=Depends(get_routing),
    pois=Depends(get_pois),
):
    trip = _get_trip(db, user, trip_id)
    generator.generate(db, trip, user.preferences, routing, pois)
    db.commit()
    db.refresh(trip)
    return trip_json(trip, user.preferences.budget_total_nok)


@app.post("/trips/{trip_id}/choose")
def choose_variant(trip_id: int, body: ChooseVariant, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    trip = _get_trip(db, user, trip_id)
    if body.variant_id not in [v.id for v in trip.variants]:
        raise HTTPException(422, "Varianten hører ikke til planen")
    trip.chosen_variant_id = body.variant_id
    trip.status = "chosen"
    db.commit()
    return {"id": trip.id, "status": trip.status, "chosen_variant_id": trip.chosen_variant_id}


@app.post("/trips/{trip_id}/evaluation", status_code=201)
def create_evaluation(trip_id: int, body: EvaluationIn, db: Session = Depends(get_db),
                      user: models.User = Depends(get_current_user)):
    trip = _get_trip(db, user, trip_id)
    if trip.evaluation:
        raise HTTPException(409, "Allerede evaluert")
    trip.evaluation = models.Evaluation(rating=body.rating, text=body.text)
    trip.status = "completed"  # DATA-01: evaluering lukker sløyfen
    db.commit()
    return {"trip_id": trip.id, "rating": body.rating, "status": trip.status}


@app.get("/me/preferences")
def get_preferences(user: models.User = Depends(get_current_user)):
    p = user.preferences
    return {
        "party_adults": p.party_adults, "party_children_ages": p.party_children_ages,
        "dog": p.dog, "vehicle": p.vehicle, "interests": p.interests,
        "budget_total_nok": p.budget_total_nok,
        "max_drive_mins_per_leg": p.max_drive_mins_per_leg,
        "day_start": p.day_start, "day_end": p.day_end,
        "lodging_types": p.lodging_types,
    }


@app.put("/me/preferences")
def put_preferences(body: PreferencesIn, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    p = db.get(models.Preferences, user.id)
    for key, value in body.model_dump().items():
        setattr(p, key, value)
    db.commit()
    return get_preferences(user=user)


@app.get("/pois/search")
def search_pois(q: str = "", pois=Depends(get_pois)):
    return [
        {"id": p.id, "name": p.name, "lat": p.lat, "lon": p.lon,
         "category": p.category, "price_level": p.price_level}
        for p in pois.search(q)
    ]


@app.get("/geocode")
def geocode(q: str = "", geocoder=Depends(get_geocoder)):
    return [
        {"name": h.name, "lat": h.lat, "lon": h.lon, "municipality": h.municipality}
        for h in geocoder.search(q)
    ]


# ---------- Auth-endepunkter ----------

class LoginRequest(BaseModel):
    email: str = Field(pattern=r".+@.+\..+")


class VerifyRequest(BaseModel):
    token: str


@app.post("/auth/request-link")
def request_login_link(body: LoginRequest, db: Session = Depends(get_db)):
    token = secrets.token_urlsafe(32)
    db.add(models.LoginToken(
        email=body.email.lower().strip(),
        token=token,
        expires_at=utcnow() + timedelta(minutes=15),
    ))
    db.commit()
    link = f"{os.environ.get('APP_BASE_URL', 'http://localhost:5173')}/?login_token={token}"
    _email_sender.send_login_link(body.email, link)
    response: dict = {"sent": True}
    if os.environ.get("AUTH_MODE", "dev") == "dev":
        response["dev_link"] = link  # kun i dev: gjør flyten testbar uten e-post
    return response


@app.post("/auth/verify")
def verify_login_token(body: VerifyRequest, db: Session = Depends(get_db)):
    login = db.scalar(
        select(models.LoginToken).where(models.LoginToken.token == body.token))
    if not login or login.used or login.expires_at.replace(tzinfo=None) < utcnow().replace(tzinfo=None):
        raise HTTPException(401, "Ugyldig eller utløpt innloggingslenke")
    login.used = True
    user = _get_or_create_user(db, login.email)
    session_token = secrets.token_urlsafe(32)
    db.add(models.ApiSession(user_id=user.id, token=session_token))
    db.commit()
    return {"token": session_token, "email": user.email}
