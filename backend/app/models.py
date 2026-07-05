"""Datamodell – speiler docs/mvp-spec.md kap. 2.

SQLite i utvikling/test; Postgres+PostGIS i produksjon (korridorsøket bor i
PoiProvider, så geografien lekker ikke inn hit).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    preferences: Mapped[Preferences | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    trip_plans: Mapped[list[TripPlan]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Preferences(Base):
    __tablename__ = "preferences"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    party_adults: Mapped[int] = mapped_column(Integer, default=2)
    party_children_ages: Mapped[list] = mapped_column(JSON, default=list)
    dog: Mapped[bool] = mapped_column(Boolean, default=False)
    # {"type": "petrol|diesel|ev", "consumption_per_100km": 6.5, "range_km": null}
    vehicle: Mapped[dict] = mapped_column(JSON, default=dict)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    budget_total_nok: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drive_mins_per_leg: Mapped[int] = mapped_column(Integer, default=300)
    day_start: Mapped[str] = mapped_column(String, default="09:00")
    day_end: Mapped[str] = mapped_column(String, default="20:00")
    lodging_types: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="preferences")


class TripPlan(Base):
    __tablename__ = "trip_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    origin: Mapped[dict] = mapped_column(JSON)  # {"name", "lat", "lon"}
    destination: Mapped[dict] = mapped_column(JSON)
    waypoints: Mapped[list] = mapped_column(JSON, default=list)
    start_date: Mapped[str] = mapped_column(String)  # ISO-dato
    days: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="draft")  # draft|chosen|completed
    chosen_variant_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # PREF-27: fravalgte POI-er huskes per plan og ekskluderes ved regenerering
    excluded_poi_ids: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="trip_plans")
    variants: Mapped[list[RouteVariant]] = relationship(
        back_populates="trip_plan", cascade="all, delete-orphan"
    )
    evaluation: Mapped[Evaluation | None] = relationship(
        back_populates="trip_plan", cascade="all, delete-orphan", uselist=False
    )


class RouteVariant(Base):
    __tablename__ = "route_variants"
    id: Mapped[int] = mapped_column(primary_key=True)
    trip_plan_id: Mapped[int] = mapped_column(ForeignKey("trip_plans.id"))
    kind: Mapped[str] = mapped_column(String)  # fastest|cheapest|scenic
    total_km: Mapped[float] = mapped_column(Float)
    total_drive_mins: Mapped[int] = mapped_column(Integer)
    total_cost_nok: Mapped[float] = mapped_column(Float)
    scenic_score: Mapped[float] = mapped_column(Float)

    trip_plan: Mapped[TripPlan] = relationship(back_populates="variants")
    legs: Mapped[list[Leg]] = relationship(
        back_populates="variant", cascade="all, delete-orphan", order_by="Leg.day_index"
    )
    cost_items: Mapped[list[CostItem]] = relationship(
        back_populates="variant", cascade="all, delete-orphan"
    )


class Leg(Base):
    __tablename__ = "legs"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("route_variants.id"))
    day_index: Mapped[int] = mapped_column(Integer)
    geometry: Mapped[list] = mapped_column(JSON)  # [[lon, lat], ...]
    drive_mins: Mapped[int] = mapped_column(Integer)
    km: Mapped[float] = mapped_column(Float)

    variant: Mapped[RouteVariant] = relationship(back_populates="legs")
    stops: Mapped[list[Stop]] = relationship(
        back_populates="leg", cascade="all, delete-orphan", order_by="Stop.order"
    )


class Stop(Base):
    __tablename__ = "stops"
    id: Mapped[int] = mapped_column(primary_key=True)
    leg_id: Mapped[int] = mapped_column(ForeignKey("legs.id"))
    poi_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)  # activity|lodging|food|rest|sight
    arrival: Mapped[str] = mapped_column(String)  # "HH:MM"
    departure: Mapped[str] = mapped_column(String)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer)

    leg: Mapped[Leg] = relationship(back_populates="stops")


class CostItem(Base):
    __tablename__ = "cost_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("route_variants.id"))
    leg_id: Mapped[int | None] = mapped_column(ForeignKey("legs.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String)  # fuel|toll|ferry|lodging|activity|food
    amount_nok: Mapped[float] = mapped_column(Float)
    is_estimate: Mapped[bool] = mapped_column(Boolean, default=True)

    variant: Mapped[RouteVariant] = relationship(back_populates="cost_items")
    leg: Mapped[Leg | None] = relationship()


class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    trip_plan_id: Mapped[int] = mapped_column(ForeignKey("trip_plans.id"), unique=True)
    rating: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, default="")

    trip_plan: Mapped[TripPlan] = relationship(back_populates="evaluation")
