from app.recommendations.domain import Candidate, Coordinates, RecommendationQuery
from app.recommendations.scoring import filter_candidates, haversine_km, score_candidate


def candidate(**overrides) -> Candidate:
    values = {
        "code": "zj-hangzhou-west-lake",
        "coordinates": Coordinates(latitude=30.25, longitude=120.15),
        "coordinate_verified": True,
        "suitable_months": [3, 4, 5, 9, 10, 11],
        "categories": ["人文", "景色"],
        "season_tags": ["旺季"],
        "crowd_tags": ["人多"],
        "transport_modes": ["高铁"],
        "min_budget": 600,
        "max_budget": 2200,
        "min_days": 2,
        "max_days": 3,
        "quality_score": 0.9,
    }
    values.update(overrides)
    return Candidate(**values)


def query(**overrides) -> RecommendationQuery:
    values = {
        "origin": Coordinates(latitude=31.2304, longitude=121.4737),
        "month": 4,
    }
    values.update(overrides)
    return RecommendationQuery(**values)


def test_haversine_distance_between_shanghai_and_hangzhou() -> None:
    distance = haversine_km(
        Coordinates(31.2304, 121.4737),
        Coordinates(30.25, 120.15),
    )

    assert 150 < distance < 190


def test_hard_filters_exclude_distance_month_and_history() -> None:
    places = [
        candidate(code="keep"),
        candidate(code="too-far", coordinates=Coordinates(39.9, 116.4)),
        candidate(code="wrong-month", suitable_months=[7, 8]),
        candidate(code="avoided"),
        candidate(code="visited"),
        candidate(code="revisit"),
        candidate(code="unverified", coordinate_verified=False),
    ]

    result = filter_candidates(
        query(max_distance_km=500),
        places,
        statuses={"avoided": "avoid", "visited": "visited", "revisit": "revisit"},
    )

    assert [item.code for item in result] == ["keep", "revisit"]


def test_hard_filters_respect_budget_days_and_include_visited() -> None:
    places = [
        candidate(code="fits"),
        candidate(code="expensive", min_budget=5000),
        candidate(code="too-long", min_days=5),
        candidate(code="visited"),
    ]

    result = filter_candidates(
        query(max_budget=3000, available_days=3, include_visited=True),
        places,
        statuses={"visited": "visited"},
    )

    assert [item.code for item in result] == ["fits", "visited"]


def test_distance_range_includes_lower_bound_and_excludes_upper_bound() -> None:
    origin = Coordinates(latitude=0, longitude=0)
    places = [
        candidate(code="below-range", coordinates=Coordinates(0, 0.5)),
        candidate(code="at-lower-bound", coordinates=Coordinates(0, 1.0)),
        candidate(code="inside-range", coordinates=Coordinates(0, 1.5)),
        candidate(code="at-upper-bound", coordinates=Coordinates(0, 2.0)),
    ]

    result = filter_candidates(
        query(origin=origin, min_distance_km=100, max_distance_km=200),
        places,
        statuses={},
    )

    assert [item.code for item in result] == ["at-lower-bound", "inside-range"]


def test_score_breakdown_uses_declared_weights() -> None:
    breakdown = score_candidate(
        query(
            preferred_categories=["人文", "景色"],
            preferred_seasons=["旺季"],
            preferred_crowds=["人多"],
            preferred_transport=["高铁"],
            max_budget=2200,
            available_days=3,
        ),
        candidate(),
    )

    assert breakdown.weights == {
        "climate": 0.30,
        "preferences": 0.25,
        "distance_transport": 0.15,
        "days_budget": 0.15,
        "crowd_season": 0.10,
        "quality": 0.05,
    }
    assert round(sum(breakdown.contributions.values()), 6) == round(breakdown.total, 6)
    assert 0.8 < breakdown.total <= 1.0
