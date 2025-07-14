from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ITSupportException(Exception):
    """Base exception for IT Support System."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(ITSupportException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.field = field
        super().__init__(message, details)


class NotAuthorizedException(ITSupportException):
    """Exception for authorization errors."""
    pass


class NotFoundException(ITSupportException):
    """Exception for resource not found errors."""
    pass


class ConflictException(ITSupportException):
    """Exception for conflict errors."""
    pass


class MLServiceException(ITSupportException):
    """Exception for ML service errors."""
    pass


class DatabaseException(ITSupportException):
    """Exception for database errors."""
    pass


# HTTP exception handlers
def create_http_exception(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create HTTP exception with consistent format."""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "error_code": error_code,
            "details": details or {},
        }
    )


def validation_error(message: str, field: Optional[str] = None) -> HTTPException:
    """Create validation error HTTP exception."""
    return create_http_exception(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
        error_code="VALIDATION_ERROR",
        details={"field": field} if field else {}
    )


def unauthorized_error(message: str = "Unauthorized") -> HTTPException:
    """Create unauthorized HTTP exception."""
    return create_http_exception(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message=message,
        error_code="UNAUTHORIZED"
    )


def forbidden_error(message: str = "Forbidden") -> HTTPException:
    """Create forbidden HTTP exception."""
    return create_http_exception(
        status_code=status.HTTP_403_FORBIDDEN,
        message=message,
        error_code="FORBIDDEN"
    )


def not_found_error(message: str = "Resource not found") -> HTTPException:
    """Create not found HTTP exception."""
    return create_http_exception(
        status_code=status.HTTP_404_NOT_FOUND,
        message=message,
        error_code="NOT_FOUND"
    )


def conflict_error(message: str = "Conflict") -> HTTPException:
    """Create conflict HTTP exception."""
    return create_http_exception(
        status_code=status.HTTP_409_CONFLICT,
        message=message,
        error_code="CONFLICT"
    )


def internal_server_error(message: str = "Internal server error") -> HTTPException:
    """Create internal server error HTTP exception."""
    return create_http_exception(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=message,
        error_code="INTERNAL_ERROR"
    )


def service_unavailable_error(message: str = "Service unavailable") -> HTTPException:
    """Create service unavailable HTTP exception."""
    return create_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message=message,
        error_code="SERVICE_UNAVAILABLE"
    )