from collections.abc import Iterator
from fastapi.testclient import TestClient
from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import AdministrativeRegion, Destination
from app.main import create_app

def test_destination_list_and_detail(db_session):
    db_session.add(AdministrativeRegion(code='110000',name='北京',level='province'))
    place=Destination(code='beijing-palace',name='故宫',summary='明清宫殿',latitude=39.9,longitude=116.4,region_code='110000',categories=['人文'],suitable_months=[4,5,9,10],season_tags=[],crowd_tags=['人多'],transport_modes=['地铁'],climate={},min_budget=100,max_budget=1000,min_days=1,max_days=2,quality_score=.9,data_version='v1',coordinate_verified=True,coordinate_source='test')
    db_session.add(place);db_session.commit()
    def override()->Iterator: yield db_session
    app=create_app();app.dependency_overrides[get_db]=override;app.dependency_overrides[get_current_user_id]=lambda:1
    with TestClient(app) as client:
        listing=client.get('/destinations',params={'search':'故宫'})
        detail=client.get(f'/destinations/{place.id}')
    assert listing.json()['items'][0]['code']=='beijing-palace'
    assert detail.json()['name']=='故宫'
