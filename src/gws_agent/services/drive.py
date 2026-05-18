"""Drive service for Google Workspace.

Single Responsibility: Drive file operations via gws CLI.
"""
import json
from typing import Any

from loguru import logger

from gws_agent.services.base import GWSBaseService


class DriveService(GWSBaseService):
    """Drive service for file operations.

    Handles:
    - Listing files
    - Searching files
    """

    def __init__(self):
        """Initialize Drive service."""
        logger.info("DriveService initialized")

    async def list_files(
        self, credentials: dict | None, max_results: int = 10, query: str | None = None
    ) -> list[dict[str, Any]]:
        """List Drive files.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            max_results: Maximum number of files
            query: Drive search query

        Returns:
            List of files with id, name, mimeType, etc.
        """
        params = {"pageSize": max_results}
        if query:
            params["q"] = query

        result = await self._run_gws(
            credentials,
            "drive", "files", "list",
            "--params", json.dumps(params)
        )

        if "error" in result:
            return []

        return result.get("files", [])

    async def search(self, credentials: dict | None, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search Drive files.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            query: Search query (file name or content)
            max_results: Maximum number of results

        Returns:
            List of matching files
        """
        # Escape query for Drive API
        drive_query = f"name contains '{query}' or fullText contains '{query}'"
        return await self.list_files(credentials, max_results=max_results, query=drive_query)
