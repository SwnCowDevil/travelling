import logging
from collections.abc import Awaitable, Callable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.schemas import RerankRequest, RerankResult
from app.destinations.models import Destination
from app.footprints.models import DestinationStatus
from app.recommendations.domain import Candidate, Coordinates, RecommendationQuery
from app.recommendations.models import RecommendationSession
from app.recommendations.schemas import (
    RecommendationCreate,
    RecommendationItem,
    RecommendationResponse,
)
from app.recommendations.scoring import filter_candidates, score_candidate

Reranker = Callable[[RerankRequest], Awaitable[RerankResult]]
logger = logging.getLogger(__name__)


def _candidate(destination: Destination) -> Candidate:
    return Candidate(
        code=destination.code,
        coordinates=Coordinates(destination.latitude, destination.longitude),
        coordinate_verified=destination.coordinate_verified,
        suitable_months=destination.suitable_months,
        categories=destination.categories,
        season_tags=destination.season_tags,
        crowd_tags=destination.crowd_tags,
        transport_modes=destination.transport_modes,
        min_budget=destination.min_budget,
        max_budget=destination.max_budget,
        min_days=destination.min_days,
        max_days=destination.max_days,
        quality_score=destination.quality_score,
    )


def _query(body: RecommendationCreate) -> RecommendationQuery:
    return RecommendationQuery(
        origin=Coordinates(body.origin_latitude, body.origin_longitude),
        month=body.month,
        min_distance_km=body.min_distance_km,
        max_distance_km=body.max_distance_km,
        max_budget=body.max_budget,
        available_days=body.available_days,
        include_visited=body.include_visited,
        preferred_categories=body.preferred_categories,
        preferred_seasons=body.preferred_seasons,
        preferred_crowds=body.preferred_crowds,
        preferred_transport=body.preferred_transport,
        sort_mode=body.sort_mode,
    )


def _sorted_codes(query: RecommendationQuery, destinations: Sequence[Destination]) -> list[str]:
    scored = [(_candidate(place), score_candidate(query, _candidate(place))) for place in destinations]
    if query.sort_mode == "nearest":
        scored.sort(key=lambda pair: pair[1].distance_km)
    elif query.sort_mode == "farthest":
        scored.sort(key=lambda pair: pair[1].distance_km, reverse=True)
    else:
        scored.sort(key=lambda pair: pair[1].total, reverse=True)
    return [candidate.code for candidate, _score in scored]


async def _select_batch(
    *,
    query: RecommendationQuery,
    origin_name: str,
    candidates: list[Destination],
    reranker: Reranker | None,
) -> tuple[list[Destination], str, dict[str, str]]:
    reasons: dict[str, str] = {}
    if reranker is not None and len(candidates) >= 3:
        request = RerankRequest(
            month=query.month,
            origin=origin_name,
            candidate_ids=[place.code for place in candidates[:12]],
            preferences=(
                query.preferred_categories
                + query.preferred_seasons
                + query.preferred_crowds
                + query.preferred_transport
            ),
        )
        try:
            result = await reranker(request)
            lookup = {place.code: place for place in candidates}
            reasons = {item.destination_id: item.reason for item in result.items}
            return [lookup[item.destination_id] for item in result.items], "ai", reasons
        except Exception:
            logger.exception("AI recommendation rerank failed; using rule fallback")
    return candidates[:3], "rules", reasons


def _response_items(
    query: RecommendationQuery,
    destinations: Sequence[Destination],
    reasons: dict[str, str],
) -> list[RecommendationItem]:
    items: list[RecommendationItem] = []
    for place in destinations:
        score = score_candidate(query, _candidate(place))
        items.append(RecommendationItem(
            destination_id=place.id,
            code=place.code,
            name=place.name,
            summary=place.summary,
            distance_km=round(score.distance_km, 1),
            score=round(score.total, 4),
            reason=reasons.get(place.code),
        ))
    return items


async def create_recommendation(
    session: Session,
    *,
    user_id: int,
    body: RecommendationCreate,
    reranker: Reranker | None,
) -> RecommendationResponse:
    query = _query(body)
    destinations = list(session.scalars(select(Destination)).all())
    status_rows = session.execute(
        select(Destination.code, DestinationStatus.status)
        .join(DestinationStatus, DestinationStatus.destination_id == Destination.id)
        .where(DestinationStatus.user_id == user_id)
    ).all()
    allowed = filter_candidates(
        query, [_candidate(place) for place in destinations], dict(status_rows)
    )
    allowed_codes = {candidate.code for candidate in allowed}
    eligible = [place for place in destinations if place.code in allowed_codes]
    ordered_codes = _sorted_codes(query, eligible)
    lookup = {place.code: place for place in eligible}
    ordered = [lookup[code] for code in ordered_codes]
    selected, source, reasons = await _select_batch(
        query=query, origin_name=body.origin_name, candidates=ordered, reranker=reranker
    )
    items = _response_items(query, selected, reasons)
    record = RecommendationSession(
        user_id=user_id,
        query=body.model_dump(mode="json"),
        candidate_codes=ordered_codes,
        shown_codes=[item.code for item in items],
        batches=[{"source": source, "items": [item.model_dump() for item in items]}],
        source=source,
        data_version=max((place.data_version for place in eligible), default="unknown"),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return RecommendationResponse(
        session_id=record.id,
        source=source,
        items=items,
        has_more=len(record.shown_codes) < len(record.candidate_codes),
    )


async def next_recommendation_batch(
    session: Session,
    *,
    record: RecommendationSession,
    reranker: Reranker | None,
) -> RecommendationResponse:
    body = RecommendationCreate.model_validate(record.query)
    query = _query(body)
    remaining_codes = [code for code in record.candidate_codes if code not in record.shown_codes]
    destinations = list(session.scalars(
        select(Destination).where(Destination.code.in_(remaining_codes))
    ).all())
    lookup = {place.code: place for place in destinations}
    ordered = [lookup[code] for code in remaining_codes if code in lookup]
    selected, source, reasons = await _select_batch(
        query=query, origin_name=body.origin_name, candidates=ordered, reranker=reranker
    )
    items = _response_items(query, selected, reasons)
    record.shown_codes = [*record.shown_codes, *[item.code for item in items]]
    record.batches = [
        *record.batches,
        {"source": source, "items": [item.model_dump() for item in items]},
    ]
    record.source = source
    session.commit()
    return RecommendationResponse(
        session_id=record.id,
        source=source,
        items=items,
        has_more=len(record.shown_codes) < len(record.candidate_codes),
    )
