"""Concrete Seitron authentication helper.

The pyseitron library only ships an ``AbstractAuth`` base class — the actual
login endpoint is implementation specific. This module performs a username /
password login against the Seitron cloud and injects a Bearer token on every
request. The exact login URL / payload is based on the common pattern used by
the Hi, Comfort mobile app; adjust :data:`LOGIN_PATH` and
:meth:`SeitronAuth._login` if your deployment differs.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from aiohttp import ClientResponseError, ClientSession
from pyseitron.auth import AbstractAuth

_LOGGER = logging.getLogger(__name__)

LOGIN_PATH = "auth/login"
TOKEN_REFRESH_MARGIN = 30


class SeitronAuthError(Exception):
    """Raised when login against the Seitron cloud fails."""


class SeitronAuth(AbstractAuth):
    """Username / password based authentication for the Seitron cloud."""

    def __init__(
        self,
        websession: ClientSession,
        host: str,
        username: str,
        password: str,
    ) -> None:
        super().__init__(websession, host.rstrip("/"))
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def async_get_access_token(self) -> str:
        """Return a valid access token, logging in / refreshing as needed."""
        async with self._lock:
            if (
                self._access_token
                and time.monotonic() < self._expires_at - TOKEN_REFRESH_MARGIN
            ):
                return self._access_token
            await self._login()
            assert self._access_token is not None
            return self._access_token

    async def _login(self) -> None:
        """Exchange username / password for a Bearer token."""
        url = f"{self.host}/{LOGIN_PATH}"
        payload: dict[str, Any] = {
            "username": self._username,
            "password": self._password,
        }
        try:
            async with self.websession.post(url, json=payload) as resp:
                if resp.status in (401, 403):
                    raise SeitronAuthError("Invalid username or password")
                resp.raise_for_status()
                data = await resp.json()
        except ClientResponseError as err:
            raise SeitronAuthError(f"Login HTTP error: {err}") from err
        except (TimeoutError, OSError) as err:
            raise SeitronAuthError(f"Cannot reach Seitron API: {err}") from err

        token = data.get("access_token") or data.get("token")
        if not token:
            raise SeitronAuthError("Login response did not include an access token")

        self._access_token = token
        self._refresh_token = data.get("refresh_token")
        expires_in = int(data.get("expires_in", 3600))
        self._expires_at = time.monotonic() + expires_in
        _LOGGER.debug("Seitron login OK, token expires in %ss", expires_in)

    async def async_validate(self) -> None:
        """Force a login round-trip; used by the config flow."""
        async with self._lock:
            await self._login()
