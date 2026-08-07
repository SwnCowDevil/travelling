from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.auth.router import get_wechat_client
from app.core.config import settings
from app.auth.wechat import WechatExchangeError, WechatSession
from app.db.session import get_db
from app.main import create_app
from app.users.models import User


@dataclass
class FakeWechatClient:
    result: WechatSession | Exception

    async def exchange(self, code: str) -> WechatSession:
        if isinstance(self.result, Exception):
            raise self.result
        assert code == "wx-code"
        return self.result


def build_client(db_session, fake_wechat: FakeWechatClient) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_wechat_client] = lambda: fake_wechat
    return TestClient(app)


def test_login_creates_user_and_returns_bearer(db_session) -> None:
    fake = FakeWechatClient(WechatSession(openid="openid-1", session_key="private"))
    response = build_client(db_session, fake).post(
        "/auth/wechat",
        json={"code": "wx-code"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert "private" not in response.json()["access_token"]
    assert db_session.query(User).filter_by(openid="openid-1").one()


def test_login_maps_wechat_failure_to_stable_error(db_session) -> None:
    fake = FakeWechatClient(WechatExchangeError("invalid code"))
    response = build_client(db_session, fake).post(
        "/auth/wechat",
        json={"code": "bad-code"},
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "WECHAT_LOGIN_FAILED"


def test_dev_login_is_disabled_by_default(db_session) -> None:
    client = build_client(db_session, FakeWechatClient(WechatExchangeError("unused")))
    response = client.post("/auth/dev")
    assert response.status_code == 404


def test_dev_login_returns_token_only_when_enabled(db_session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "enable_dev_auth", True)
    client = build_client(db_session, FakeWechatClient(WechatExchangeError("unused")))
    response = client.post("/auth/dev")
    assert response.status_code == 200
    assert response.json()["access_token"]
    assert db_session.query(User).filter_by(openid="local-development-user").one()
