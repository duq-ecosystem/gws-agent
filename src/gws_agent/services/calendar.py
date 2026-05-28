"""Calendar service for Google Workspace.

Single Responsibility: Calendar event operations via direct Google API HTTP calls.
"""
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from gws_agent.services.base import GWSBaseService, GWSError


CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
MAX_DESCRIPTION_LENGTH = 200


class CalendarService(GWSBaseService):
    """Calendar service for event operations.

    Handles:
    - Listing events
    - Creating events
    - Updating events
    - Deleting events
    """

    def __init__(self):
        """Initialize Calendar service."""
        logger.info("CalendarService initialized")

    async def list_events(self, credentials: dict | None, max_results: int = 10) -> list[dict[str, Any]]:
        """List upcoming calendar events.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            max_results: Maximum number of events

        Returns:
            List of calendar events
        """
        if not credentials:
            raise GWSError("No credentials provided")

        url = f"{CALENDAR_API_BASE}/calendars/primary/events"
        now = datetime.now(timezone.utc).isoformat()
        params = {
            "maxResults": max_results,
            "timeMin": now,
            "singleEvents": True,
            "orderBy": "startTime",
        }

        result = await self._google_api_request(credentials, "GET", url, params=params)

        if "error" in result:
            error_msg = result["error"]
            logger.error(f"Calendar list_events failed: {error_msg}")
            raise GWSError(f"Calendar API error: {error_msg}")

        items = result.get("items", [])
        if not items:
            return []

        # Format events for easier consumption
        events = []
        for item in items[:max_results]:
            start = item.get("start", {})
            end = item.get("end", {})
            events.append({
                "id": item.get("id"),
                "summary": item.get("summary", "Без названия"),
                "start": start.get("dateTime") or start.get("date"),
                "end": end.get("dateTime") or end.get("date"),
                "location": item.get("location", ""),
                "description": item.get("description", "")[:MAX_DESCRIPTION_LENGTH] if item.get("description") else "",
            })

        return events

    async def create_event(
        self,
        credentials: dict | None,
        summary: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
        location: str | None = None,
    ) -> str | None:
        """Create calendar event.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            summary: Event title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            description: Event description
            location: Event location

        Returns:
            Event ID if created, None otherwise
        """
        if not credentials:
            return None

        url = f"{CALENDAR_API_BASE}/calendars/primary/events"
        event_data = {
            "summary": summary,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }
        if description:
            event_data["description"] = description
        if location:
            event_data["location"] = location

        result = await self._google_api_request(credentials, "POST", url, json_body=event_data)

        if "error" in result:
            return None
        return result.get("id")

    async def update_event(
        self,
        credentials: dict | None,
        event_id: str,
        summary: str | None = None,
        description: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        location: str | None = None,
    ) -> bool:
        """Update calendar event.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            event_id: Event ID
            summary: New title (optional)
            description: New description (optional)
            start_time: New start time (ISO format, optional)
            end_time: New end time (ISO format, optional)
            location: New location (optional)

        Returns:
            True if updated
        """
        if not credentials:
            return False

        event_data: dict[str, Any] = {}
        if summary is not None:
            event_data["summary"] = summary
        if description is not None:
            event_data["description"] = description
        if start_time is not None:
            event_data["start"] = {"dateTime": start_time}
        if end_time is not None:
            event_data["end"] = {"dateTime": end_time}
        if location is not None:
            event_data["location"] = location

        if not event_data:
            return False

        url = f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}"
        result = await self._google_api_request(credentials, "PATCH", url, json_body=event_data)

        return "error" not in result

    async def delete_event(self, credentials: dict | None, event_id: str) -> bool:
        """Delete calendar event.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            event_id: Event ID

        Returns:
            True if deleted
        """
        if not credentials:
            return False

        url = f"{CALENDAR_API_BASE}/calendars/primary/events/{event_id}"
        result = await self._google_api_request(credentials, "DELETE", url)

        return "error" not in result
