"""Google Workspace services package.

SOLID-compliant decomposition of GWS functionality:
- GmailService: Email operations
- CalendarService: Calendar operations
- DriveService: Drive file operations
- TasksService: Tasks operations
- GWSService: Facade combining all services

Each service follows Single Responsibility Principle.
"""

from gws_agent.services.base import GWSBaseService, GWSError
from gws_agent.services.gmail import GmailService
from gws_agent.services.calendar import CalendarService
from gws_agent.services.drive import DriveService
from gws_agent.services.tasks import TasksService
from gws_agent.services.facade import GWSService, get_gws_service

__all__ = [
    "GWSBaseService",
    "GWSError",
    "GmailService",
    "CalendarService",
    "DriveService",
    "TasksService",
    "GWSService",
    "get_gws_service",
]
