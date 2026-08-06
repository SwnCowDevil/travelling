from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import Destination
from app.visits.models import VisitRecord
from app.visits.schemas import (
    VisitCreate,
    VisitDeleteRequest,
    VisitListResponse,
    VisitResponse,
    VisitUpdate,
)
from app.visits.service import (
    DuplicateVisitDate,
    LastVisitRequiresStatusChange,
    count_visits,
    create_visit,
    delete_visit,
    update_visit,
)

router = APIRouter(prefix="/visit-records", tags=["visit-records"])


def _response(session: Session, record: VisitRecord) -> VisitResponse:
    return VisitResponse(
        id=record.id,
        destination_id=record.destination_id,
        visited_on=record.visited_on,
        note=record.note,
        visit_count=count_visits(session, record.user_id, record.destination_id),
    )


@router.get("", response_model=VisitListResponse)
def list_visits(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> VisitListResponse:
    records = session.scalars(select(VisitRecord).where(
        VisitRecord.user_id == user_id
    ).order_by(VisitRecord.visited_on.desc(), VisitRecord.id.desc())).all()
    return VisitListResponse(items=[_response(session, record) for record in records])


@router.post("", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
def add_visit(
    body: VisitCreate,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> VisitResponse:
    if session.get(Destination, body.destination_id) is None:
        raise HTTPException(404, detail={"code": "DESTINATION_NOT_FOUND"})
    try:
        change = create_visit(
            session, user_id, body.destination_id, body.visited_on,
            note=body.note, idempotency_key=body.idempotency_key,
            confirm_duplicate=body.confirm_duplicate,
        )
    except DuplicateVisitDate as exc:
        raise HTTPException(409, detail={"code": "DUPLICATE_VISIT_DATE"}) from exc
    return _response(session, change.record)


@router.patch("/{visit_id}", response_model=VisitResponse)
def patch_visit(
    visit_id: int,
    body: VisitUpdate,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> VisitResponse:
    try:
        record = update_visit(
            session, user_id, visit_id, visited_on=body.visited_on,
            note=body.note, confirm_duplicate=body.confirm_duplicate,
        )
    except DuplicateVisitDate as exc:
        raise HTTPException(409, detail={"code": "DUPLICATE_VISIT_DATE"}) from exc
    if record is None:
        raise HTTPException(404, detail={"code": "VISIT_NOT_FOUND"})
    return _response(session, record)


@router.delete("/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_visit(
    visit_id: int,
    body: VisitDeleteRequest | None = Body(default=None),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> Response:
    try:
        delete_visit(
            session, user_id, visit_id,
            replacement_status=body.replacement_status if body else None,
        )
    except LastVisitRequiresStatusChange as exc:
        raise HTTPException(
            409, detail={"code": "LAST_VISIT_REQUIRES_STATUS_CHANGE"}
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
