from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Candidate:
    code: str
    coordinates: Coordinates
    coordinate_verified: bool
    suitable_months: list[int] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    season_tags: list[str] = field(default_factory=list)
    crowd_tags: list[str] = field(default_factory=list)
    transport_modes: list[str] = field(default_factory=list)
    min_budget: int | None = None
    max_budget: int | None = None
    min_days: int | None = None
    max_days: int | None = None
    quality_score: float = 0.5


@dataclass(frozen=True)
class RecommendationQuery:
    origin: Coordinates
    month: int
    min_distance_km: float | None = None
    max_distance_km: float | None = None
    max_budget: int | None = None
    available_days: int | None = None
    include_visited: bool = False
    preferred_categories: list[str] = field(default_factory=list)
    preferred_seasons: list[str] = field(default_factory=list)
    preferred_crowds: list[str] = field(default_factory=list)
    preferred_transport: list[str] = field(default_factory=list)
    sort_mode: Literal["recommended", "nearest", "farthest"] = "recommended"


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    weights: dict[str, float]
    contributions: dict[str, float]
    distance_km: float
