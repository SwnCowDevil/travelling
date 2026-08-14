from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


AIRequestPurpose = Literal["rerank", "guide_fast", "guide_deep"]


@dataclass(frozen=True)
class AIRequestPolicy:
    thinking_enabled: bool | None
    max_tokens: int


_MAX_TOKENS: dict[AIRequestPurpose, int] = {
    "rerank": 1200,
    "guide_fast": 6000,
    "guide_deep": 12000,
}


def request_policy(base_url: str, purpose: AIRequestPurpose) -> AIRequestPolicy:
    hostname = (urlparse(base_url).hostname or "").lower()
    thinking_enabled = None
    if hostname == "api.deepseek.com":
        thinking_enabled = purpose == "guide_deep"
    return AIRequestPolicy(
        thinking_enabled=thinking_enabled,
        max_tokens=_MAX_TOKENS[purpose],
    )
