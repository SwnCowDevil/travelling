from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.ai.crypto import TokenCipher
from app.ai.router import get_connection_test, get_current_user_id, get_token_cipher
from app.db.session import get_db
from app.main import create_app
from app.users.models import User


def test_profile_api_saves_masks_and_deletes_personal_config(db_session) -> None:
    db_session.add(User(id=11, openid="profile-api-user"))
    db_session.commit()
    async def successful_test(**_kwargs) -> None:
        return None

    def override_db() -> Iterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: 11
    app.dependency_overrides[get_token_cipher] = lambda: TokenCipher(
        b"0123456789abcdef0123456789abcdef"
    )
    app.dependency_overrides[get_connection_test] = lambda: successful_test

    with TestClient(app) as client:
        initial = client.get("/ai-profile")
        saved = client.put("/ai-profile", json={
            "token": "sk-user-secret-6789",
            "base_url": "https://api.example.com/v1",
            "model": "custom-model",
            "group_note": "chatgpt",
        })
        fetched = client.get("/ai-profile")
        deleted = client.delete("/ai-profile")
        fallback = client.get("/ai-profile")

    assert initial.json()["mode"] == "system"
    assert saved.status_code == 200
    assert saved.json()["masked_token"] == "****6789"
    assert "sk-user-secret" not in saved.text
    assert fetched.json()["mode"] == "personal"
    assert deleted.status_code == 204
    assert fallback.json()["mode"] == "system"
