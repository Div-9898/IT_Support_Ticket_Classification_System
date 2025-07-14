from .auth import (
    auth_service,
    get_current_user,
    require_role,
    require_admin,
    require_agent_or_admin,
    get_current_user_optional,
    can_access_ticket,
    can_modify_ticket,
    can_assign_ticket,
    can_resolve_ticket,
)
from .logging import setup_logging, get_logger
from .exceptions import (
    ITSupportException,
    ValidationException,
    NotAuthorizedException,
    NotFoundException,
    ConflictException,
)

__all__ = [
    "auth_service",
    "get_current_user",
    "require_role",
    "require_admin",
    "require_agent_or_admin",
    "get_current_user_optional",
    "can_access_ticket",
    "can_modify_ticket",
    "can_assign_ticket",
    "can_resolve_ticket",
    "setup_logging",
    "get_logger",
    "ITSupportException",
    "ValidationException",
    "NotAuthorizedException",
    "NotFoundException",
    "ConflictException",
]