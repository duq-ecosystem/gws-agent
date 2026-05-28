"""Gmail service for Google Workspace.

Single Responsibility: Email operations via direct Google API HTTP calls.
"""
import base64
from email.mime.text import MIMEText
from typing import Any

from loguru import logger

from gws_agent.services.base import GWSBaseService, GWSError


GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"


class GmailService(GWSBaseService):
    """Gmail service for email operations.

    Handles:
    - Listing messages
    - Getting message details
    - Sending emails
    - Marking as read
    """

    def __init__(self):
        """Initialize Gmail service."""
        logger.info("GmailService initialized")

    async def list_messages(
        self, credentials: dict | None, max_results: int = 10, query: str | None = None
    ) -> list[dict[str, Any]]:
        """List Gmail messages.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            max_results: Maximum number of messages to return
            query: Gmail search query (e.g., "is:unread", "from:user@example.com")

        Returns:
            List of message objects with id, threadId, snippet, etc.
        """
        if not credentials:
            raise GWSError("No credentials provided")

        url = f"{GMAIL_API_BASE}/users/me/messages"
        params = {"maxResults": max_results}
        if query:
            params["q"] = query

        result = await self._google_api_request(credentials, "GET", url, params=params)

        if "error" in result:
            error_msg = result["error"]
            logger.error(f"Gmail list_messages failed: {error_msg}")
            raise GWSError(f"Gmail API error: {error_msg}")

        messages = result.get("messages", [])

        # Get details for each message
        detailed = []
        for msg in messages[:max_results]:
            detail = await self.get_message(credentials, msg["id"])
            if detail:
                detailed.append(detail)

        return detailed

    async def get_message(self, credentials: dict | None, message_id: str) -> dict[str, Any] | None:
        """Get Gmail message details.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            message_id: Message ID

        Returns:
            Message details with headers, snippet, etc.
        """
        if not credentials:
            return None

        url = f"{GMAIL_API_BASE}/users/me/messages/{message_id}"
        params = {"format": "metadata"}

        result = await self._google_api_request(credentials, "GET", url, params=params)

        if "error" in result:
            logger.warning(f"Gmail get_message failed for {message_id}: {result['error']}")
            return None

        # Extract useful info from headers
        headers = {h["name"]: h["value"] for h in result.get("payload", {}).get("headers", [])}

        return {
            "id": result.get("id"),
            "threadId": result.get("threadId"),
            "snippet": result.get("snippet"),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "labels": result.get("labelIds", []),
        }

    async def get_unread(self, credentials: dict | None, max_results: int = 10) -> list[dict[str, Any]]:
        """Get unread Gmail messages.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            max_results: Maximum number of messages

        Returns:
            List of unread messages
        """
        return await self.list_messages(credentials, max_results=max_results, query="is:unread")

    async def send(self, credentials: dict | None, to: str, subject: str, body: str) -> bool:
        """Send email via Gmail.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)

        Returns:
            True if sent successfully
        """
        if not credentials:
            return False

        # Build MIME message
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        # Encode as base64url
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        url = f"{GMAIL_API_BASE}/users/me/messages/send"
        result = await self._google_api_request(
            credentials, "POST", url, json_body={"raw": raw}
        )

        return "error" not in result

    async def mark_read(self, credentials: dict | None, message_id: str) -> bool:
        """Mark message as read.

        Args:
            credentials: User credentials (access_token, refresh_token, token_type)
            message_id: Message ID

        Returns:
            True if successful
        """
        if not credentials:
            return False

        url = f"{GMAIL_API_BASE}/users/me/messages/{message_id}/modify"
        result = await self._google_api_request(
            credentials, "POST", url, json_body={"removeLabelIds": ["UNREAD"]}
        )

        return "error" not in result
