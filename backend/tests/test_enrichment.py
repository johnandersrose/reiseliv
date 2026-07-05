"""Enhetstester for ruteberikelsen, mot sample-datafilene i backend/data/."""
from app.enrichment import RouteEnricher, min_distance_km
from app.providers.base import RouteCandidate

# Grov rute Oslo→Bergen via Rv7/Hardangervidda-sample-linjen og Hardangerbrua.
RV7_ROUTE = [
    [10.75, 59.91], [10.34, 59.96],           # ut av Oslo, forbi Sollihøgda-bommen
    [9.50, 60.20], [8.50, 60.45],
    [7.87, 60.51], [7.72, 60.36], [7.42, 60.38], [7.28, 60.42], [7.07, 60.47],
    [6.85, 60.44],                             # Hardangerbrua
    [6.34, 60.42], [5.90, 60.40], [5.32, 60.39],
]
# Samme trasé forskjøvet 1° nord: treffer verken bommer eller turistveger.
OFF_ROUTE = [[lon, lat + 1.0] for lon, lat in RV7_ROUTE]

enricher = RouteEnricher()


def test_min_distance_on_line_is_zero():
    line = [[7.0, 60.0], [8.0, 60.0]]
    assert min_distance_km([7.5, 60.0], line) < 0.01
    assert 50 < min_distance_km([7.5, 60.5], line) < 60  # ~0,5° lat ≈ 55,7 km


def test_toll_counts_stations_on_route_only():
    total = enricher.toll_nok(RV7_ROUTE)
    # Oslo vest + Sollihøgda + Hardangerbrua ligger på ruten; Stavanger ikke.
    assert total == 24 + 34 + 133
    assert enricher.toll_nok(OFF_ROUTE) == 0


def test_ferry_detection():
    # Ruten passerer nær Kvanndal–Utne-punktet, men ikke Moss–Horten.
    assert enricher.ferry_nok(RV7_ROUTE) == 120
    assert enricher.ferry_nok(OFF_ROUTE) == 0


def test_scenic_overlap_high_on_turistveg_low_off():
    on = enricher.scenic_overlap(RV7_ROUTE)
    off = enricher.scenic_overlap(OFF_ROUTE)
    assert on > 0.5   # store deler av traseen følger sample-turistvegene
    assert off == 0.0


def test_scenic_score_bounded_and_ordered():
    s_on = enricher.scenic_score(RV7_ROUTE, km=460, viewpoints=6)
    s_off = enricher.scenic_score(OFF_ROUTE, km=460, viewpoints=0)
    assert 0.0 <= s_off < s_on <= 1.0


def test_enrich_replaces_candidate_fields():
    c = RouteCandidate(
        name="test", geometry=RV7_ROUTE, km=460, drive_mins=420,
        toll_nok=0, ferry_nok=0, scenic_score=0.0,
    )
    enriched = enricher.enrich(c, viewpoints=4)
    assert enriched.toll_nok == 191
    assert enriched.ferry_nok == 120
    assert enriched.scenic_score > 0.4
    assert c.toll_nok == 0  # original uendret (replace, ikke mutasjon)


def test_sample_data_flag():
    assert enricher.uses_sample_data() is True
