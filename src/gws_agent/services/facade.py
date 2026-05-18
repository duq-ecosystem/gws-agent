"""GWS Facade for backward compatibility.

Provides unified interface combining all GWS services.
This allows existing code to work without changes while
internally delegating to specialized services.
"""
from typing import Any

from loguru import logger

from gws_agent.services.gmail import GmailService
from gws_agent.services.calendar import CalendarService
from gws_agent.services.drive import DriveService
from gws_agent.services.tasks import TasksService


class GWSService:
    """Facade combining all GWS services for backward compatibility.

    This class delegates to specialized services:
    - GmailService: Email operations
    - CalendarService: Calendar operations
    - DriveService: Drive operations
    - TasksService: Tasks operations

    New code should use individual services directly.
    """

    def __init__(self):
        """Initialize GWS facade with all services."""
        self._gmail = GmailService()
        self._calendar = CalendarService()
        self._drive = DriveService()
        self._tasks = TasksService()
        logger.info("GWSService facade initialized (all 4 services)")

    # === GMAIL (delegated) ===

    async def gmail_list_messages(
        self, credentials: dict | None, max_results: int = 10, query: str | None = None
    ) -> list[dict[str, Any]]:
        """List Gmail messages."""
        return await self._gmail.list_messages(credentials, max_results, query)

    async def gmail_get_message(self, credentials: dict | None, message_id: str) -> dict[str, Any] | None:
        """Get Gmail message details."""
        return await self._gmail.get_message(credentials, message_id)

    async def gmail_get_unread(self, credentials: dict | None, max_results: int = 10) -> list[dict[str, Any]]:
        """Get unread Gmail messages."""
        return await self._gmail.get_unread(credentials, max_results)

    async def gmail_send(self, credentials: dict | None, to: str, subject: str, body: str) -> bool:
        """Send email via Gmail."""
        return await self._gmail.send(credentials, to, subject, body)

    async def gmail_mark_read(self, credentials: dict | None, message_id: str) -> bool:
        """Mark message as read."""
        return await self._gmail.mark_read(credentials, message_id)

    # === CALENDAR (delegated) ===

    async def calendar_list_events(self, credentials: dict | None, max_results: int = 10) -> list[dict[str, Any]]:
        """List upcoming calendar events."""
        return await self._calendar.list_events(credentials, max_results)

    async def calendar_create_event(
        self,
        credentials: dict | None,
        summary: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
        location: str | None = None,
    ) -> str | None:
        """Create calendar event."""
        return await self._calendar.create_event(
            credentials, summary, start_time, end_time, description, location
        )

    async def calendar_update_event(
        self,
        credentials: dict | None,
        event_id: str,
        summary: str | None = None,
        description: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        location: str | None = None,
    ) -> bool:
        """Update calendar event."""
        return await self._calendar.update_event(
            credentials, event_id, summary, description, start_time, end_time, location
        )

    async def calendar_delete_event(self, credentials: dict | None, event_id: str) -> bool:
        """Delete calendar event."""
        return await self._calendar.delete_event(credentials, event_id)

    # === DRIVE (delegated) ===

    async def drive_list_files(
        self, credentials: dict | None, max_results: int = 10, query: str | None = None
    ) -> list[dict[str, Any]]:
        """List Drive files."""
        return await self._drive.list_files(credentials, max_results, query)

    async def drive_search(self, credentials: dict | None, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search Drive files."""
        return await self._drive.search(credentials, query, max_results)

    # === TASKS (delegated) ===

    async def tasks_list(self, credentials: dict | None, max_results: int = 10) -> list[dict[str, Any]]:
        """List tasks from default task list."""
        return await self._tasks.list_tasks(credentials, max_results)

    async def tasks_create(
        self,
        credentials: dict | None,
        title: str,
        notes: str | None = None,
        due: str | None = None,
    ) -> str | None:
        """Create a new task."""
        return await self._tasks.create(credentials, title, notes, due)

    async def tasks_update(
        self,
        credentials: dict | None,
        task_id: str,
        title: str | None = None,
        notes: str | None = None,
        due: str | None = None,
        status: str | None = None,
    ) -> bool:
        """Update an existing task."""
        return await self._tasks.update(credentials, task_id, title, notes, due, status)

    async def tasks_delete(self, credentials: dict | None, task_id: str) -> bool:
        """Delete a task."""
        return await self._tasks.delete(credentials, task_id)

    async def tasks_complete(self, credentials: dict | None, task_id: str) -> bool:
        """Mark task as completed."""
        return await self._tasks.complete(credentials, task_id)

    # === Service accessors for direct access ===

    @property
    def gmail(self) -> GmailService:
        """Get Gmail service for direct access."""
        return self._gmail

    @property
    def calendar(self) -> CalendarService:
        """Get Calendar service for direct access."""
        return self._calendar

    @property
    def drive(self) -> DriveService:
        """Get Drive service for direct access."""
        return self._drive

    @property
    def tasks(self) -> TasksService:
        """Get Tasks service for direct access."""
        return self._tasks


# Singleton instance
_gws_service: GWSService | None = None


def get_gws_service() -> GWSService:
    """Get or create GWSService singleton."""
    global _gws_service
    if _gws_service is None:
        _gws_service = GWSService()
    return _gws_service
