from __future__ import annotations

import hashlib
from typing import Any

import aiohttp

from .const import API_BASE, MD5_KEY


class FanJuAuthError(Exception):
    pass


class FanJuApiError(Exception):
    pass


class FanJuApi:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._token: str | None = None

    @staticmethod
    def _md5_hex(s: str) -> str:
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    async def ensure_token(self) -> str:
        if self._token:
            return self._token

        pwd_md5 = self._md5_hex(self._password + MD5_KEY)  # як у плагіні  [oai_citation:7‡GitHub](https://raw.githubusercontent.com/slavvka/homebridge-fanju-fjw4/master/src/api/weather-api.ts)
        payload = {"email": self._username, "pwd": pwd_md5}

        async with self._session.post(f"{API_BASE}/account/login", json=payload, timeout=20) as resp:
            data: dict[str, Any] = await resp.json(content_type=None)

        if data.get("status") != 0:
            raise FanJuAuthError(data.get("errorMsg") or "Login failed")

        token = (data.get("content") or {}).get("token")
        if not token:
            raise FanJuAuthError("No token in response")

        self._token = token
        return token

    async def _get(self, path: str) -> dict[str, Any]:
        token = await self.ensure_token()
        headers = {"emaxToken": token}  # як у плагіні  [oai_citation:8‡GitHub](https://raw.githubusercontent.com/slavvka/homebridge-fanju-fjw4/master/src/api/weather-api.ts)

        async with self._session.get(f"{API_BASE}{path}", headers=headers, timeout=20) as resp:
            data: dict[str, Any] = await resp.json(content_type=None)

        if data.get("status") != 0:
            raise FanJuApiError(f"Bad API response: {data}")

        return data

    async def get_bound_device(self) -> dict[str, Any]:
        return await self._get("/weather/getBindedDevice")  #  [oai_citation:9‡GitHub](https://raw.githubusercontent.com/slavvka/homebridge-fanju-fjw4/master/src/api/weather-api.ts)

    async def get_realtime(self) -> dict[str, Any]:
        return await self._get("/weather/devData/getRealtime")  #  [oai_citation:10‡GitHub](https://raw.githubusercontent.com/slavvka/homebridge-fanju-fjw4/master/src/api/weather-api.ts)
