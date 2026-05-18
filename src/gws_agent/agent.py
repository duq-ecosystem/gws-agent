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
            url=config.get_public_url(),
            version="1.0.0",
            capabilities=AgentCapabilities(
                streaming=False,
                push_notifications=False,
                state_transition_history=False,
            ),
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
        """Return tool definitions for A2A."""
        return [
            ToolDefinition(
                name="gmail_unread",
                description="Get unread emails",
                input_schema={
                    "type": "object",
                    "properties": {"max_results": {"type": "integer", "default": 10}},
                },
            ),
            ToolDefinition(
                name="gmail_send",
                description="Send email",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["to", "subject", "body"],
                },
            ),
            ToolDefinition(
                name="gmail_mark_read",
                description="Mark email as read",
                input_schema={
                    "type": "object",
                    "properties": {"message_id": {"type": "string"}},
                    "required": ["message_id"],
                },
            ),
            ToolDefinition(
                name="calendar_list",
                description="List calendar events",
                input_schema={
                    "type": "object",
                    "properties": {"max_results": {"type": "integer", "default": 10}},
                },
            ),
            ToolDefinition(
                name="calendar_create",
                description="Create calendar event",
                input_schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["summary", "start_time", "end_time"],
                },
            ),
            ToolDefinition(
                name="calendar_update",
                description="Update calendar event",
                input_schema={
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string"},
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    },
                    "required": ["event_id"],
                },
            ),
            ToolDefinition(
                name="calendar_delete",
                description="Delete calendar event",
                input_schema={
                    "type": "object",
                    "properties": {"event_id": {"type": "string"}},
                    "required": ["event_id"],
                },
            ),
            ToolDefinition(
                name="drive_list",
                description="List Drive files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "default": 10},
                        "query": {"type": "string"},
                    },
                },
            ),
            ToolDefinition(
                name="tasks_list",
                description="List tasks",
                input_schema={
                    "type": "object",
                    "properties": {"max_results": {"type": "integer", "default": 10}},
                },
            ),
            ToolDefinition(
                name="tasks_create",
                description="Create task",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "notes": {"type": "string"},
                        "due": {"type": "string"},
                    },
                    "required": ["title"],
                },
            ),
            ToolDefinition(
                name="tasks_complete",
                description="Complete task",
                input_schema={
                    "type": "object",
                    "properties": {"task_id": {"type": "string"}},
                    "required": ["task_id"],
                },
            ),
            ToolDefinition(
                name="tasks_delete",
                description="Delete task",
                input_schema={
                    "type": "object",
                    "properties": {"task_id": {"type": "string"}},
                    "required": ["task_id"],
                },
            ),
        ]

    async def execute_tool(self, tool_name: str, args: dict[str, Any], user_id: int) -> dict[str, Any]:
        """Execute a tool with user credentials.

        Args:
            tool_name: Name of tool to execute
            args: Tool arguments
            user_id: User ID for credentials lookup

        Returns:
            Tool result
        """
        logger.info(f"[GWS] Executing: {tool_name} for user {user_id}")

        # Get credentials
        credentials = await get_user_gws_credentials(user_id)
        if not credentials:
            return {"error": "GWS_CREDENTIALS_NOT_AVAILABLE. Need to connect Google account."}

        try:
            # Route to handler
            handlers = {
                "gmail_unread": self._gmail_unread,
                "gmail_send": self._gmail_send,
                "gmail_mark_read": self._gmail_mark_read,
                "calendar_list": self._calendar_list,
                "calendar_create": self._calendar_create,
                "calendar_update": self._calendar_update,
                "calendar_delete": self._calendar_delete,
                "drive_list": self._drive_list,
                "tasks_list": self._tasks_list,
                "tasks_create": self._tasks_create,
                "tasks_complete": self._tasks_complete,
                "tasks_delete": self._tasks_delete,
            }

            handler = handlers.get(tool_name)
            if not handler:
                return {"error": f"Unknown tool: {tool_name}"}

            result = await handler(credentials, args)
            return {"content": [{"type": "text", "text": result}]}

        except Exception as e:
            logger.exception(f"[GWS] Error in {tool_name}: {e}")
            return {"error": str(e)}

    async def process(self, task: A2ATask) -> A2ATaskResult:
        """Process an A2A task."""
        try:
            context = task.context or {}
            skill_id = context.get("skill_id")
            parameters = context.get("parameters", {})
            user_id = context.get("user_id")

            if not skill_id:
                return A2ATaskResult(
                    task_id=task.id,
                    status="failed",
                    error="No skill_id in context",
                )

            if not user_id:
                return A2ATaskResult(
                    task_id=task.id,
                    status="failed",
                    error="No user_id in context",
                )

            logger.info(f"[GWS] Processing task {task.id}: {skill_id} for user {user_id}")
            result = await self.execute_tool(skill_id, parameters, user_id)

            if "error" in result:
                return A2ATaskResult(
                    task_id=task.id,
                    status="failed",
                    error=result["error"],
                )

            return A2ATaskResult(
                task_id=task.id,
                status="completed",
                result=result,
            )

        except Exception as e:
            logger.exception(f"[GWS] Task {task.id} failed: {e}")
            return A2ATaskResult(
                task_id=task.id,
                status="failed",
                error=str(e),
            )

    # =========================================================================
    # Gmail Handlers
    # =========================================================================

    async def _gmail_unread(self, creds: dict, args: dict) -> str:
        """Get unread emails."""
        max_results = args.get("max_results", 10)
        emails = await self._gws.gmail_get_unread(creds, max_results=max_results)

        if not emails:
            return "No unread emails."

        lines = []
        for i, email in enumerate(emails, 1):
            lines.append(f"{i}. From: {email.get('from', 'Unknown')}")
            lines.append(f"   Subject: {email.get('subject', 'No subject')}")
            lines.append(f"   Brief: {email.get('snippet', '')}")
            lines.append(f"   ID: {email.get('id', '')}")
            lines.append("")

        return "\n".join(lines)

    async def _gmail_send(self, creds: dict, args: dict) -> str:
        """Send email."""
        to = args.get("to", "")
        subject = args.get("subject", "")
        body = args.get("body", "")

        if not to or not subject or not body:
            return "Error: Need to, subject, and body"

        success = await self._gws.gmail_send(creds, to, subject, body)
        return f"Email sent to {to}" if success else "Failed to send email"

    async def _gmail_mark_read(self, creds: dict, args: dict) -> str:
        """Mark email as read."""
        message_id = args.get("message_id", "")
        if not message_id:
            return "Error: Need message_id"

        success = await self._gws.gmail_mark_read(creds, message_id)
        return "Email marked as read" if success else "Failed to mark as read"

    # =========================================================================
    # Calendar Handlers
    # =========================================================================

    async def _calendar_list(self, creds: dict, args: dict) -> str:
        """List calendar events."""
        max_results = args.get("max_results", 10)
        events = await self._gws.calendar_list_events(creds, max_results=max_results)

        if not events:
            return "No upcoming events"

        lines = ["Upcoming events:\n"]
        for event in events:
            lines.append(f"- {event.get('summary', 'No title')}")
            lines.append(f"  Start: {event.get('start', {})}")
            lines.append(f"  ID: {event.get('id', '')}")
            lines.append("")

        return "\n".join(lines)

    async def _calendar_create(self, creds: dict, args: dict) -> str:
        """Create calendar event."""
        summary = args.get("summary", "")
        start_time = args.get("start_time", "")
        end_time = args.get("end_time", "")
        description = args.get("description", "")

        if not summary or not start_time or not end_time:
            return "Error: Need summary, start_time, end_time"

        event_id = await self._gws.calendar_create_event(
            creds, summary=summary, start_time=start_time,
            end_time=end_time, description=description
        )
        return f"Event created: {event_id}" if event_id else "Failed to create event"

    async def _calendar_update(self, creds: dict, args: dict) -> str:
        """Update calendar event."""
        event_id = args.get("event_id", "")
        if not event_id:
            return "Error: Need event_id"

        success = await self._gws.calendar_update_event(
            creds,
            event_id=event_id,
            summary=args.get("summary"),
            description=args.get("description"),
            start_time=args.get("start_time"),
            end_time=args.get("end_time"),
        )
        return "Event updated" if success else "Failed to update event"

    async def _calendar_delete(self, creds: dict, args: dict) -> str:
        """Delete calendar event."""
        event_id = args.get("event_id", "")
        if not event_id:
            return "Error: Need event_id"

        success = await self._gws.calendar_delete_event(creds, event_id)
        return "Event deleted" if success else "Failed to delete event"

    # =========================================================================
    # Drive Handlers
    # =========================================================================

    async def _drive_list(self, creds: dict, args: dict) -> str:
        """List Drive files."""
        max_results = args.get("max_results", 10)
        query = args.get("query", "")

        if query:
            files = await self._gws.drive_search(creds, query, max_results=max_results)
        else:
            files = await self._gws.drive_list_files(creds, max_results=max_results)

        if not files:
            return "No files found"

        lines = ["Files:\n"]
        for f in files:
            lines.append(f"- {f.get('name', 'Unknown')}")
            lines.append(f"  Type: {f.get('mimeType', 'Unknown')}")
            lines.append(f"  ID: {f.get('id', '')}")
            lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # Tasks Handlers
    # =========================================================================

    async def _tasks_list(self, creds: dict, args: dict) -> str:
        """List tasks."""
        max_results = args.get("max_results", 10)
        tasks = await self._gws.tasks_list(creds, max_results=max_results)

        if not tasks:
            return "No tasks"

        lines = ["Tasks:\n"]
        for t in tasks:
            status = "[done]" if t.get("status") == "completed" else "[ ]"
            lines.append(f"{status} {t.get('title', 'No title')}")
            if t.get("due"):
                lines.append(f"  Due: {t['due']}")
            lines.append(f"  ID: {t.get('id', '')}")
            lines.append("")

        return "\n".join(lines)

    async def _tasks_create(self, creds: dict, args: dict) -> str:
        """Create task."""
        title = args.get("title", "")
        if not title:
            return "Error: Need title"

        task_id = await self._gws.tasks_create(
            creds, title=title,
            notes=args.get("notes"),
            due=args.get("due"),
        )
        return f"Task created: {title} (ID: {task_id})" if task_id else "Failed to create task"

    async def _tasks_complete(self, creds: dict, args: dict) -> str:
        """Complete task."""
        task_id = args.get("task_id", "")
        if not task_id:
            return "Error: Need task_id"

        success = await self._gws.tasks_complete(creds, task_id)
        return "Task completed" if success else "Failed to complete task"

    async def _tasks_delete(self, creds: dict, args: dict) -> str:
        """Delete task."""
        task_id = args.get("task_id", "")
        if not task_id:
            return "Error: Need task_id"

        success = await self._gws.tasks_delete(creds, task_id)
        return "Task deleted" if success else "Failed to delete task"
