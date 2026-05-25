"""GWS Agent - Google Workspace specialist.

Handles Gmail, Calendar, Drive, Tasks via A2A protocol.
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger

from duq_agent_core import (
    AgentCapabilities,
    AgentCard,
    AgentConfig,
    AgentInterface,
    AgentSkill,
    AgentTemplate,
    A2ATask,
    A2ATaskResult,
    ToolDefinition,
)

from gws_agent.credentials import get_user_gws_credentials
from gws_agent.services.facade import GWSService


class GWSAgent(AgentTemplate):
    """Google Workspace specialist agent.

    Handles email, calendar, drive, and tasks operations.
    """

    def __init__(self, config: AgentConfig):
        self._gws = GWSService()

        card = AgentCard(
            name="gws-agent",
            description="Google Workspace: Gmail, Calendar, Drive, Tasks",
            version="1.0.0",
            supported_interfaces=[
                AgentInterface(
                    url=config.get_public_url(),
                    protocol_binding="JSONRPC",
                    protocol_version="1.0",
                )
            ],
            capabilities=AgentCapabilities(
                streaming=False,
                push_notifications=False,
                state_transition_history=False,
            ),
            default_input_modes=["text/plain", "application/json"],
            default_output_modes=["text/plain", "application/json"],
            skills=self._create_skills(),
        )

        super().__init__(card, config)

    def _create_skills(self) -> list[AgentSkill]:
        """Create skill definitions for agent card."""
        return [
            # OAuth
            AgentSkill(
                id="oauth_connect",
                name="Connect Google Account",
                description="Initiate Google OAuth flow",
                tags=["oauth", "connect"],
                input_schema={"type": "object", "properties": {}},
            ),
            # Gmail
            AgentSkill(
                id="gmail_unread",
                name="Get Unread Emails",
                description="Get unread emails from Gmail",
                tags=["gmail", "email", "unread"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "default": 10},
                    },
                },
            ),
            AgentSkill(
                id="gmail_send",
                name="Send Email",
                description="Send email via Gmail",
                tags=["gmail", "email", "send"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body"},
                    },
                    "required": ["to", "subject", "body"],
                },
            ),
            AgentSkill(
                id="gmail_mark_read",
                name="Mark Email Read",
                description="Mark email as read",
                tags=["gmail", "email"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Message ID"},
                    },
                    "required": ["message_id"],
                },
            ),
            # Calendar
            AgentSkill(
                id="calendar_list",
                name="List Events",
                description="List upcoming calendar events",
                tags=["calendar", "events"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "default": 10},
                    },
                },
            ),
            AgentSkill(
                id="calendar_create",
                name="Create Event",
                description="Create calendar event",
                tags=["calendar", "events", "create"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Event title"},
                        "start_time": {"type": "string", "description": "Start (ISO 8601)"},
                        "end_time": {"type": "string", "description": "End (ISO 8601)"},
                        "description": {"type": "string", "description": "Description"},
                    },
                    "required": ["summary", "start_time", "end_time"],
                },
            ),
            AgentSkill(
                id="calendar_update",
                name="Update Event",
                description="Update calendar event",
                tags=["calendar", "events", "update"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "Event ID"},
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    },
                    "required": ["event_id"],
                },
            ),
            AgentSkill(
                id="calendar_delete",
                name="Delete Event",
                description="Delete calendar event",
                tags=["calendar", "events", "delete"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "Event ID"},
                    },
                    "required": ["event_id"],
                },
            ),
            # Drive
            AgentSkill(
                id="drive_list",
                name="List Files",
                description="List Google Drive files",
                tags=["drive", "files"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "default": 10},
                        "query": {"type": "string", "description": "Search query"},
                    },
                },
            ),
            # Tasks
            AgentSkill(
                id="tasks_list",
                name="List Tasks",
                description="List Google Tasks",
                tags=["tasks"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "default": 10},
                    },
                },
            ),
            AgentSkill(
                id="tasks_create",
                name="Create Task",
                description="Create a new task",
                tags=["tasks", "create"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "notes": {"type": "string", "description": "Notes"},
                        "due": {"type": "string", "description": "Due date (ISO 8601)"},
                    },
                    "required": ["title"],
                },
            ),
            AgentSkill(
                id="tasks_complete",
                name="Complete Task",
                description="Mark task as completed",
                tags=["tasks", "complete"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            AgentSkill(
                id="tasks_delete",
                name="Delete Task",
                description="Delete a task",
                tags=["tasks", "delete"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
        ]

    def get_tools(self) -> list[ToolDefinition]:
        """Return tool definitions with handlers."""
        return [
            ToolDefinition(
                name="gmail_unread",
                description="Get unread emails",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "max_results": {"type": "integer", "default": 10},
                    },
                    "required": ["user_id"],
                },
                handler=self._gmail_unread,
            ),
            ToolDefinition(
                name="gmail_send",
                description="Send email",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["user_id", "to", "subject", "body"],
                },
                handler=self._gmail_send,
            ),
            ToolDefinition(
                name="gmail_mark_read",
                description="Mark email as read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "message_id": {"type": "string"},
                    },
                    "required": ["user_id", "message_id"],
                },
                handler=self._gmail_mark_read,
            ),
            ToolDefinition(
                name="calendar_list",
                description="List calendar events",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "max_results": {"type": "integer", "default": 10},
                    },
                    "required": ["user_id"],
                },
                handler=self._calendar_list,
            ),
            ToolDefinition(
                name="calendar_create",
                description="Create calendar event",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "summary": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["user_id", "summary", "start_time", "end_time"],
                },
                handler=self._calendar_create,
            ),
            ToolDefinition(
                name="calendar_update",
                description="Update calendar event",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "event_id": {"type": "string"},
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    },
                    "required": ["user_id", "event_id"],
                },
                handler=self._calendar_update,
            ),
            ToolDefinition(
                name="calendar_delete",
                description="Delete calendar event",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "event_id": {"type": "string"},
                    },
                    "required": ["user_id", "event_id"],
                },
                handler=self._calendar_delete,
            ),
            ToolDefinition(
                name="drive_list",
                description="List Drive files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "max_results": {"type": "integer", "default": 10},
                        "query": {"type": "string"},
                    },
                    "required": ["user_id"],
                },
                handler=self._drive_list,
            ),
            ToolDefinition(
                name="tasks_list",
                description="List tasks",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "max_results": {"type": "integer", "default": 10},
                    },
                    "required": ["user_id"],
                },
                handler=self._tasks_list,
            ),
            ToolDefinition(
                name="tasks_create",
                description="Create task",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "title": {"type": "string"},
                        "notes": {"type": "string"},
                        "due": {"type": "string"},
                    },
                    "required": ["user_id", "title"],
                },
                handler=self._tasks_create,
            ),
            ToolDefinition(
                name="tasks_complete",
                description="Complete task",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "task_id": {"type": "string"},
                    },
                    "required": ["user_id", "task_id"],
                },
                handler=self._tasks_complete,
            ),
            ToolDefinition(
                name="tasks_delete",
                description="Delete task",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "User ID for credentials"},
                        "task_id": {"type": "string"},
                    },
                    "required": ["user_id", "task_id"],
                },
                handler=self._tasks_delete,
            ),
        ]


    # =========================================================================
    # Gmail Handlers
    # =========================================================================

    async def _gmail_unread(self, user_id: int, max_results: int = 10) -> dict:
        """Get unread emails."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        emails = await self._gws.gmail_get_unread(creds, max_results=max_results)

        if not emails:
            return {"content": [{"type": "text", "text": "No unread emails."}]}

        lines = []
        for i, email in enumerate(emails, 1):
            lines.append(f"{i}. From: {email.get('from', 'Unknown')}")
            lines.append(f"   Subject: {email.get('subject', 'No subject')}")
            lines.append(f"   Brief: {email.get('snippet', '')}")
            lines.append(f"   ID: {email.get('id', '')}")
            lines.append("")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    async def _gmail_send(self, user_id: int, to: str, subject: str, body: str) -> dict:
        """Send email."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        success = await self._gws.gmail_send(creds, to, subject, body)
        text = f"Email sent to {to}" if success else "Failed to send email"
        return {"content": [{"type": "text", "text": text}]}

    async def _gmail_mark_read(self, user_id: int, message_id: str) -> dict:
        """Mark email as read."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        success = await self._gws.gmail_mark_read(creds, message_id)
        text = "Email marked as read" if success else "Failed to mark as read"
        return {"content": [{"type": "text", "text": text}]}

    # =========================================================================
    # Calendar Handlers
    # =========================================================================

    async def _calendar_list(self, user_id: int, max_results: int = 10) -> dict:
        """List calendar events."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        events = await self._gws.calendar_list_events(creds, max_results=max_results)

        if not events:
            return {"content": [{"type": "text", "text": "No upcoming events"}]}

        lines = ["Upcoming events:\n"]
        for event in events:
            lines.append(f"- {event.get('summary', 'No title')}")
            lines.append(f"  Start: {event.get('start', {})}")
            lines.append(f"  ID: {event.get('id', '')}")
            lines.append("")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    async def _calendar_create(
        self,
        user_id: int,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
    ) -> dict:
        """Create calendar event."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        event_id = await self._gws.calendar_create_event(
            creds, summary=summary, start_time=start_time,
            end_time=end_time, description=description
        )
        text = f"Event created: {event_id}" if event_id else "Failed to create event"
        return {"content": [{"type": "text", "text": text}]}

    async def _calendar_update(
        self,
        user_id: int,
        event_id: str,
        summary: str | None = None,
        description: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """Update calendar event."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        success = await self._gws.calendar_update_event(
            creds,
            event_id=event_id,
            summary=summary,
            description=description,
            start_time=start_time,
            end_time=end_time,
        )
        text = "Event updated" if success else "Failed to update event"
        return {"content": [{"type": "text", "text": text}]}

    async def _calendar_delete(self, user_id: int, event_id: str) -> dict:
        """Delete calendar event."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        success = await self._gws.calendar_delete_event(creds, event_id)
        text = "Event deleted" if success else "Failed to delete event"
        return {"content": [{"type": "text", "text": text}]}

    # =========================================================================
    # Drive Handlers
    # =========================================================================

    async def _drive_list(self, user_id: int, max_results: int = 10, query: str = "") -> dict:
        """List Drive files."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        if query:
            files = await self._gws.drive_search(creds, query, max_results=max_results)
        else:
            files = await self._gws.drive_list_files(creds, max_results=max_results)

        if not files:
            return {"content": [{"type": "text", "text": "No files found"}]}

        lines = ["Files:\n"]
        for f in files:
            lines.append(f"- {f.get('name', 'Unknown')}")
            lines.append(f"  Type: {f.get('mimeType', 'Unknown')}")
            lines.append(f"  ID: {f.get('id', '')}")
            lines.append("")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    # =========================================================================
    # Tasks Handlers
    # =========================================================================

    async def _tasks_list(self, user_id: int, max_results: int = 10) -> dict:
        """List tasks."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        tasks = await self._gws.tasks_list(creds, max_results=max_results)

        if not tasks:
            return {"content": [{"type": "text", "text": "No tasks"}]}

        lines = ["Tasks:\n"]
        for t in tasks:
            status = "[done]" if t.get("status") == "completed" else "[ ]"
            lines.append(f"{status} {t.get('title', 'No title')}")
            if t.get("due"):
                lines.append(f"  Due: {t['due']}")
            lines.append(f"  ID: {t.get('id', '')}")
            lines.append("")

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    async def _tasks_create(
        self,
        user_id: int,
        title: str,
        notes: str = "",
        due: str = "",
    ) -> dict:
        """Create task."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        task_id = await self._gws.tasks_create(
            creds, title=title,
            notes=notes or None,
            due=due or None,
        )
        text = f"Task created: {title} (ID: {task_id})" if task_id else "Failed to create task"
        return {"content": [{"type": "text", "text": text}]}

    async def _tasks_complete(self, user_id: int, task_id: str) -> dict:
        """Complete task."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        success = await self._gws.tasks_complete(creds, task_id)
        text = "Task completed" if success else "Failed to complete task"
        return {"content": [{"type": "text", "text": text}]}

    async def _tasks_delete(self, user_id: int, task_id: str) -> dict:
        """Delete task."""
        creds = await get_user_gws_credentials(user_id)
        if not creds:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE"}

        success = await self._gws.tasks_delete(creds, task_id)
        text = "Task deleted" if success else "Failed to delete task"
        return {"content": [{"type": "text", "text": text}]}
