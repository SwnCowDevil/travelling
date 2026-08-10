import asyncio
import json
from typing import Any

import httpx
from pydantic import ValidationError

from app.ai.schemas import RerankRequest, RerankResult


class InvalidAIResponse(ValueError):
    pass


class AIClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        timeout_seconds: int = 20,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._http = http

    async def rerank(self, request: RerankRequest) -> RerankResult:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "仅在给定候选中选择并排序三个目的地。"
                        "返回 JSON：{\"items\":[{\"destination_id\":...,\"reason\":...}]}"
                    ),
                },
                {"role": "user", "content": request.model_dump_json()},
            ],
        }
        response = await self._post(payload)
        try:
            content = response["choices"][0]["message"]["content"]
            result = RerankResult.model_validate(json.loads(content))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            raise InvalidAIResponse("AI returned an invalid structured response") from exc
        allowed = set(request.candidate_ids)
        if any(item.destination_id not in allowed for item in result.items):
            raise InvalidAIResponse("AI returned a destination outside the candidate set")
        return result

    async def test_connection(self) -> None:
        payload = {
            "model": self.model,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        }
        await self._post(payload)

    async def complete_json(self, system_prompt: str, user_payload: str) -> dict[str, Any]:
        response = await self._post({
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        })
        try:
            content = response["choices"][0]["message"]["content"]
            value = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise InvalidAIResponse("AI returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise InvalidAIResponse("AI JSON root must be an object")
        return value

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        for attempt in range(2):
            try:
                if self._http is not None:
                    response = await self._http.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )
                else:
                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as http:
                        response = await http.post(
                            f"{self.base_url}/chat/completions", headers=headers, json=payload
                        )
                if response.status_code == 503:
                    try:
                        if response.json().get("error", {}).get("code") == "model_not_found":
                            response.raise_for_status()
                    except (TypeError, ValueError, AttributeError):
                        pass
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
                error_code = None
                if isinstance(exc, httpx.HTTPStatusError):
                    try:
                        error = exc.response.json().get("error")
                        if isinstance(error, dict):
                            error_code = error.get("code")
                    except (TypeError, ValueError, AttributeError):
                        pass
                retryable = isinstance(exc, httpx.TimeoutException) or (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code in {500, 502, 503, 504}
                    and not (exc.response.status_code == 503 and error_code == "model_not_found")
                )
                if attempt == 1 or not retryable:
                    raise
                await asyncio.sleep(0.5)
        raise RuntimeError("unreachable")
