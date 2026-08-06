from dataclasses import dataclass

import httpx


class WechatExchangeError(RuntimeError):
    pass


@dataclass(frozen=True)
class WechatSession:
    openid: str
    session_key: str


class WechatClient:
    endpoint = "https://api.weixin.qq.com/sns/jscode2session"

    def __init__(self, app_id: str, app_secret: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret

    async def exchange(self, code: str) -> WechatSession:
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.endpoint, params=params)
        response.raise_for_status()
        payload = response.json()
        if payload.get("errcode") or not payload.get("openid") or not payload.get("session_key"):
            raise WechatExchangeError(str(payload.get("errmsg", "invalid response")))
        return WechatSession(openid=payload["openid"], session_key=payload["session_key"])
