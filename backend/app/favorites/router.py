from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import Destination
from app.custom_destinations.service import get_custom_destination
from app.favorites.models import FavoriteGuide
from app.favorites.schemas import FavoriteGuideCreate, FavoriteGuideListResponse, FavoriteGuideResponse, FavoriteGuideUpdate
from app.favorites.service import delete_favorite, get_favorite, list_favorites, save_favorite, update_favorite

router = APIRouter(prefix="/favorite-guides", tags=["favorite-guides"])


def _response(value: FavoriteGuide) -> FavoriteGuideResponse:
    return FavoriteGuideResponse(
        id=value.id, destination_id=value.destination_id, custom_destination_id=value.custom_destination_id, destination_type=value.destination_type, generation_mode=value.generation_mode,
        payload=value.payload, destination_snapshot=value.destination_snapshot,
        created_at=value.created_at, updated_at=value.updated_at,
    )


@router.post("", response_model=FavoriteGuideResponse, status_code=status.HTTP_201_CREATED)
def create_favorite(body: FavoriteGuideCreate, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> FavoriteGuideResponse:
    if body.custom_destination_id is not None:
        destination = get_custom_destination(session, user_id, body.custom_destination_id)
        if destination is None: raise HTTPException(404, detail={"code": "CUSTOM_DESTINATION_NOT_FOUND"})
        favorite, _created = save_favorite(session, user_id, destination, body.payload, body.generation_mode, destination_type="custom")
    else:
        destination = session.get(Destination, body.destination_id)
        if destination is None: raise HTTPException(404, detail={"code": "DESTINATION_NOT_FOUND"})
        favorite, _created = save_favorite(session, user_id, destination, body.payload, body.generation_mode)
    return _response(favorite)


@router.get("", response_model=FavoriteGuideListResponse)
def list_favorite_guides(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> FavoriteGuideListResponse:
    return FavoriteGuideListResponse(items=[_response(item) for item in list_favorites(session, user_id)])


@router.get("/{favorite_id}", response_model=FavoriteGuideResponse)
def get_favorite_guide(favorite_id: int, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> FavoriteGuideResponse:
    favorite = get_favorite(session, user_id, favorite_id)
    if favorite is None:
        raise HTTPException(404, detail={"code": "FAVORITE_GUIDE_NOT_FOUND"})
    return _response(favorite)


@router.put("/{favorite_id}", response_model=FavoriteGuideResponse)
def put_favorite_guide(favorite_id: int, body: FavoriteGuideUpdate, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> FavoriteGuideResponse:
    favorite = update_favorite(session, user_id, favorite_id, body.payload, body.generation_mode)
    if favorite is None:
        raise HTTPException(404, detail={"code": "FAVORITE_GUIDE_NOT_FOUND"})
    return _response(favorite)


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_guide(favorite_id: int, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> Response:
    if not delete_favorite(session, user_id, favorite_id):
        raise HTTPException(404, detail={"code": "FAVORITE_GUIDE_NOT_FOUND"})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
