import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TokenCipher:
    def __init__(self, key: bytes) -> None:
        if len(key) not in (16, 24, 32):
            raise ValueError("AES key must be 16, 24, or 32 bytes")
        self._cipher = AESGCM(key)

    @classmethod
    def from_base64(cls, encoded_key: str) -> "TokenCipher":
        return cls(base64.urlsafe_b64decode(encoded_key.encode("ascii")))

    def encrypt(self, token: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self._cipher.encrypt(nonce, token.encode("utf-8"), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, encrypted_token: str) -> str:
        payload = base64.urlsafe_b64decode(encrypted_token.encode("ascii"))
        return self._cipher.decrypt(payload[:12], payload[12:], None).decode("utf-8")


def mask_token(token: str) -> str:
    return f"****{token[-4:]}" if token else ""
