from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import Destination
from app.destinations.schemas import DestinationList, DestinationRead

router=APIRouter(prefix='/destinations',tags=['destinations'])

@router.get('',response_model=DestinationList)
def list_destinations(search:str|None=None,region_code:str|None=None,month:int|None=Query(default=None,ge=1,le=12),_user_id:int=Depends(get_current_user_id),session:Session=Depends(get_db))->DestinationList:
    query=select(Destination)
    if search: query=query.where(Destination.name.contains(search))
    if region_code: query=query.where(Destination.region_code==region_code)
    places=list(session.scalars(query.order_by(Destination.quality_score.desc())).all())
    if month: places=[place for place in places if not place.suitable_months or month in place.suitable_months]
    return DestinationList(items=places)

@router.get('/{destination_id}',response_model=DestinationRead)
def get_destination(destination_id:int,_user_id:int=Depends(get_current_user_id),session:Session=Depends(get_db))->Destination:
    place=session.get(Destination,destination_id)
    if place is None: raise HTTPException(404,detail={'code':'DESTINATION_NOT_FOUND'})
    return place
