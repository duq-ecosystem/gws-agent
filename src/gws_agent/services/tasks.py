"""Tasks service for Google Workspace.

Single Responsibility: Google Tasks operations via direct Google API HTTP calls.
"""
from typing import Any

from loguru import logger

from gws_agent.services.base import GWSBaseService


TASKS_API_BASE = "https://tasks.googleapis.com/tasks/v1"


class TasksService(GWSBaseService):
    """Tasks service for task operations.

    Handles:
    - Listing tasks
    - Creating tasks
    - Updating tasks
    - Deleting tasks
    - Completing tasks
    """

    def __init__(self):
        """Initialize Tasks service."""
        logger.info("TasksService initialized")

    async def _get_default_tasklist_id(self, credentials: dict | None) -> str | None:
        """Get the default task list ID."""
        if not credentials:
            return None

        url = f"{TASKS_API_BASE}/users/@me/lists"
        params = {"maxResults": 1}

        result = await self._google_api_request(credentials, "GET", url, params=params)

        if "error" in result:
            return None

        task_lists = result.get("items", [])
        if not task_lists:
            return None

        return task_lists[0].get("id")

    async def list_tasks(self, credentials: dict | None, max_results: int = 10) -> list[dict[str, Any]]:
        """List tasks from default task list.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            max_results: Maximum number of tasks

        Returns:
            List of tasks
        """
        task_list_id = await self._get_default_tasklist_id(credentials)
        if not task_list_id:
            return []

        url = f"{TASKS_API_BASE}/lists/{task_list_id}/tasks"
        params = {"maxResults": max_results}

        result = await self._google_api_request(credentials, "GET", url, params=params)

        if "error" in result:
            return []

        return result.get("items", [])

    async def create(
        self,
        credentials: dict | None,
        title: str,
        notes: str | None = None,
        due: str | None = None,
    ) -> str | None:
        """Create a new task.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            title: Task title
            notes: Task notes/description
            due: Due date (RFC 3339 format, e.g., "2024-12-31T12:00:00Z")

        Returns:
            Task ID if created, None otherwise
        """
        task_list_id = await self._get_default_tasklist_id(credentials)
        if not task_list_id:
            return None

        url = f"{TASKS_API_BASE}/lists/{task_list_id}/tasks"
        task_data: dict[str, Any] = {"title": title}
        if notes:
            task_data["notes"] = notes
        if due:
            task_data["due"] = due

        result = await self._google_api_request(credentials, "POST", url, json_body=task_data)

        if "error" in result:
            return None
        return result.get("id")

    async def update(
        self,
        credentials: dict | None,
        task_id: str,
        title: str | None = None,
        notes: str | None = None,
        due: str | None = None,
        status: str | None = None,  # "needsAction" or "completed"
    ) -> bool:
        """Update an existing task.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            task_id: Task ID
            title: New title (optional)
            notes: New notes (optional)
            due: New due date (optional)
            status: New status (optional)

        Returns:
            True if updated successfully
        """
        task_list_id = await self._get_default_tasklist_id(credentials)
        if not task_list_id:
            return False

        task_data: dict[str, Any] = {}
        if title is not None:
            task_data["title"] = title
        if notes is not None:
            task_data["notes"] = notes
        if due is not None:
            task_data["due"] = due
        if status is not None:
            task_data["status"] = status

        if not task_data:
            return False

        url = f"{TASKS_API_BASE}/lists/{task_list_id}/tasks/{task_id}"
        result = await self._google_api_request(credentials, "PATCH", url, json_body=task_data)

        return "error" not in result

    async def delete(self, credentials: dict | None, task_id: str) -> bool:
        """Delete a task.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            task_id: Task ID

        Returns:
            True if deleted successfully
        """
        task_list_id = await self._get_default_tasklist_id(credentials)
        if not task_list_id:
            return False

        url = f"{TASKS_API_BASE}/lists/{task_list_id}/tasks/{task_id}"
        result = await self._google_api_request(credentials, "DELETE", url)

        return "error" not in result

    async def complete(self, credentials: dict | None, task_id: str) -> bool:
        """Mark task as completed.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            task_id: Task ID

        Returns:
            True if completed successfully
        """
        return await self.update(credentials, task_id, status="completed")
