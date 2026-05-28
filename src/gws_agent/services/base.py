"""Base class for Google Workspace services.

Provides shared functionality for credential management and Google API HTTP calls.
Uses direct HTTP via httpx instead of CLI wrapper.
"""
import os
from typing import Any

import httpx
from loguru import logger


class GWSError(Exception):
    """Error from Google Workspace API.

    Raised when Google API returns an error (auth failure, API error, etc.).
    This prevents silent failures from being masked as "no data".
    """

    pass


class GWSBaseService:
    """Base class with shared GWS functionality.

    Uses direct HTTP calls to Google APIs instead of CLI wrapper.
    Handles OAuth token refresh automatically.
    """

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

    async def _refresh_access_token(self, credentials: dict) -> str | None:
        """Refresh OAuth access token using refresh_token.

        Args:
            credentials: Dict with refresh_token

        Returns:
            New access_token or None if refresh failed
        """
        refresh_token = credentials.get("refresh_token")
        if not refresh_token:
            logger.warning("No refresh_token in credentials")
            return None

        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            logger.error("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set")
            return None

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.GOOGLE_TOKEN_URL,
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.debug("Successfully refreshed access token")
                    return data.get("access_token")
                else:
                    logger.error(f"Token refresh failed: {response.status_code} {response.text[:200]}")
                    return None
            except Exception as e:
                logger.error(f"Token refresh error: {e}")
                return None

    async def _google_api_request(
        self,
        credentials: dict,
        method: str,
        url: str,
        params: dict | None = None,
        json_body: dict | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Make authenticated request to Google API.

        Args:
            credentials: User credentials with access_token/refresh_token
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            url: Full Google API URL
            params: Query parameters
            json_body: JSON body for POST/PUT/PATCH
            timeout: Request timeout

        Returns:
            Parsed JSON response or error dict
        """
        # Get or refresh access token
        access_token = credentials.get("access_token")
        if not access_token:
            access_token = await self._refresh_access_token(credentials)
            if not access_token:
                return {"error": "Google аккаунт не подключён. Скажи 'подключи гугл' для авторизации."}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=timeout,
                )

                # Handle token expiration - retry with refreshed token
                if response.status_code == 401:
                    logger.info("Access token expired, refreshing...")
                    access_token = await self._refresh_access_token(credentials)
                    if not access_token:
                        return {"error": "Не удалось обновить Google токен. Переподключи аккаунт."}

                    headers["Authorization"] = f"Bearer {access_token}"
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_body,
                        timeout=timeout,
                    )

                if response.status_code in (200, 201, 204):
                    if response.content:
                        return response.json()
                    return {"success": True}
                else:
                    error_msg = response.text[:500]
                    logger.error(f"Google API error: {response.status_code} {error_msg}")
                    return {"error": f"Google API error: {response.status_code}"}

            except httpx.TimeoutException:
                logger.error(f"Google API timeout: {url}")
                return {"error": "Таймаут запроса к Google"}
            except Exception as e:
                logger.error(f"Google API request failed: {e}")
                return {"error": str(e)}
