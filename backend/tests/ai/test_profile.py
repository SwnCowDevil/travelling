import pytest
from pydantic import ValidationError

from app.ai.crypto import TokenCipher, mask_token
from app.ai.models import AIProfile
from app.ai.profile import ProfileConnectionError, save_personal_profile
from app.ai.schemas import AIProfileUpdate
from app.users.models import User


def test_token_cipher_hides_plaintext_and_mask_only_shows_last_four() -> None:
    cipher = TokenCipher(b"0123456789abcdef0123456789abcdef")

    encrypted = cipher.encrypt("sk-private-token-1234")

    assert "sk-private-token-1234" not in encrypted
    assert cipher.decrypt(encrypted) == "sk-private-token-1234"
    assert mask_token("sk-private-token-1234") == "****1234"


def test_personal_profile_rejects_insecure_provider_url() -> None:
    with pytest.raises(ValidationError):
        AIProfileUpdate(
            token="sk-test",
            base_url="http://provider.example/v1",
            model="model",
        )


def test_personal_profile_keeps_normal_request_timeout_limit() -> None:
    with pytest.raises(ValidationError):
        AIProfileUpdate(
            token="sk-test",
            base_url="https://provider.example/v1",
            model="model",
            timeout_seconds=90,
        )


@pytest.mark.asyncio
async def test_failed_connection_does_not_replace_existing_profile(db_session) -> None:
    cipher = TokenCipher(b"0123456789abcdef0123456789abcdef")
    db_session.add(User(id=7, openid="profile-test-user"))
    db_session.flush()
    existing = AIProfile(
        user_id=7,
        base_url="https://old.example/v1",
        model="old-model",
        protocol="chat_completions",
        timeout_seconds=20,
        group_note="deepseek",
        encrypted_token=cipher.encrypt("sk-old-token"),
        token_last_four="oken",
        connection_status="ok",
    )
    db_session.add(existing)
    db_session.commit()

    async def failing_test(**_kwargs) -> None:
        raise RuntimeError("provider unavailable")

    with pytest.raises(ProfileConnectionError):
        await save_personal_profile(
            db_session,
            user_id=7,
            base_url="https://new.example/v1",
            model="new-model",
            token="sk-new-token",
            protocol="chat_completions",
            timeout_seconds=10,
            group_note="chatgpt",
            cipher=cipher,
            connection_test=failing_test,
        )

    db_session.expire_all()
    saved = db_session.query(AIProfile).filter_by(user_id=7).one()
    assert saved.base_url == "https://old.example/v1"
    assert cipher.decrypt(saved.encrypted_token) == "sk-old-token"
