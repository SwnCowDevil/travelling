from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import AdministrativeRegion, Destination
from app.footprints.models import DestinationStatus, RegionStatus
from app.footprints.schemas import StatusResponse, StatusUpdate
from app.footprints.service import (
    InvalidFootprintTransition,
    clear_status,
    set_destination_status,
    set_region_status,
)
from app.visits.service import count_visits

router = APIRouter(tags=["footprints"])


@router.put("/destination-statuses/{destination_id}", response_model=StatusResponse)
def put_destination_status(
    destination_id: int,
    body: StatusUpdate,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> StatusResponse:
    if session.get(Destination, destination_id) is None:
        raise HTTPException(404, detail={"code": "DESTINATION_NOT_FOUND"})
    try:
        result = set_destination_status(
            session,
            user_id,
            destination_id,
            body.status,
            visit_count=count_visits(session, user_id, destination_id),
        )
    except InvalidFootprintTransition as exc:
        raise HTTPException(
            409, detail={"code": "REVISIT_REQUIRES_VISIT", "message": "想再去需要到访记录"}
        ) from exc
    return StatusResponse(status=result.status.status, warning_code=result.warning_code)


@router.delete(
    "/destination-statuses/{destination_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_destination_status(
    destination_id: int,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> Response:
    record = session.scalar(select(DestinationStatus).where(
        DestinationStatus.user_id == user_id,
        DestinationStatus.destination_id == destination_id,
    ))
    clear_status(session, record)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/region-statuses/{region_code}", response_model=StatusResponse)
def put_region_status(
    region_code: str,
    body: StatusUpdate,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> StatusResponse:
    if session.get(AdministrativeRegion, region_code) is None:
        raise HTTPException(404, detail={"code": "REGION_NOT_FOUND"})
    result = set_region_status(session, user_id, region_code, body.status)
    return StatusResponse(status=result.status.status)


@router.delete("/region-statuses/{region_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region_status(
    region_code: str,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> Response:
    record = session.scalar(select(RegionStatus).where(
        RegionStatus.user_id == user_id,
        RegionStatus.region_code == region_code,
    ))
    clear_status(session, record)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
