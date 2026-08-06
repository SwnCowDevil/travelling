from math import asin, cos, radians, sin, sqrt
from typing import Mapping, Sequence

from app.recommendations.domain import (
    Candidate,
    Coordinates,
    RecommendationQuery,
    ScoreBreakdown,
)

WEIGHTS = {
    "climate": 0.30,
    "preferences": 0.25,
    "distance_transport": 0.15,
    "days_budget": 0.15,
    "crowd_season": 0.10,
    "quality": 0.05,
}


def haversine_km(origin: Coordinates, target: Coordinates) -> float:
    radius_km = 6371.0088
    lat1, lat2 = radians(origin.latitude), radians(target.latitude)
    delta_lat = radians(target.latitude - origin.latitude)
    delta_lon = radians(target.longitude - origin.longitude)
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * radius_km * asin(sqrt(value))


def filter_candidates(
    query: RecommendationQuery,
    candidates: Sequence[Candidate],
    statuses: Mapping[str, str],
) -> list[Candidate]:
    result: list[Candidate] = []
    for candidate in candidates:
        status = statuses.get(candidate.code)
        if status == "avoid":
            continue
        if status == "visited" and not query.include_visited:
            continue
        if candidate.suitable_months and query.month not in candidate.suitable_months:
            continue
        if query.max_budget is not None and candidate.min_budget is not None:
            if candidate.min_budget > query.max_budget:
                continue
        if query.available_days is not None and candidate.min_days is not None:
            if candidate.min_days > query.available_days:
                continue
        if query.max_distance_km is not None:
            if not candidate.coordinate_verified:
                continue
            if haversine_km(query.origin, candidate.coordinates) > query.max_distance_km:
                continue
        result.append(candidate)
    return result


def _overlap_score(preferred: Sequence[str], actual: Sequence[str]) -> float:
    if not preferred:
        return 1.0
    matches = len(set(preferred) & set(actual))
    return matches / len(set(preferred))


def score_candidate(
    query: RecommendationQuery,
    candidate: Candidate,
) -> ScoreBreakdown:
    distance = haversine_km(query.origin, candidate.coordinates)
    climate = 1.0 if not candidate.suitable_months or query.month in candidate.suitable_months else 0.0
    preferences = _overlap_score(query.preferred_categories, candidate.categories)
    transport = _overlap_score(query.preferred_transport, candidate.transport_modes)
    distance_scale = query.max_distance_km or 2000.0
    distance_score = max(0.0, 1.0 - distance / max(distance_scale, 1.0))
    distance_transport = (distance_score + transport) / 2
    budget = 1.0
    if query.max_budget is not None and candidate.min_budget is not None:
        budget = min(1.0, query.max_budget / max(candidate.min_budget, 1))
    days = 1.0
    if query.available_days is not None and candidate.min_days is not None:
        days = min(1.0, query.available_days / max(candidate.min_days, 1))
    days_budget = (days + budget) / 2
    crowd = _overlap_score(query.preferred_crowds, candidate.crowd_tags)
    season = _overlap_score(query.preferred_seasons, candidate.season_tags)
    crowd_season = (crowd + season) / 2
    components = {
        "climate": climate,
        "preferences": preferences,
        "distance_transport": distance_transport,
        "days_budget": days_budget,
        "crowd_season": crowd_season,
        "quality": min(1.0, max(0.0, candidate.quality_score)),
    }
    contributions = {name: components[name] * weight for name, weight in WEIGHTS.items()}
    return ScoreBreakdown(
        total=sum(contributions.values()),
        weights=dict(WEIGHTS),
        contributions=contributions,
        distance_km=distance,
    )
