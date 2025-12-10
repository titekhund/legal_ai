"""
Custom exceptions and exception handlers for the application
"""
from typing import Any, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse


# ============================================================================
# Custom Exception Classes
# ============================================================================


class LegalAIException(Exception):
    """Base exception for all Legal AI exceptions"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class TaxCodeNotFoundError(LegalAIException):
    """Raised when tax code document or section is not found"""

    def __init__(
        self,
        message: str = "Tax code document not found",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class LLMError(LegalAIException):
    """Raised when LLM service encounters an error"""

    def __init__(
        self,
        message: str = "LLM service error",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class RateLimitError(LegalAIException):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class ValidationError(LegalAIException):
    """Raised when validation fails"""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ConfigurationError(LegalAIException):
    """Raised when configuration is invalid or missing"""

    def __init__(
        self,
        message: str = "Configuration error",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class VectorDBError(LegalAIException):
    """Raised when vector database encounters an error"""

    def __init__(
        self,
        message: str = "Vector database error",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class CitationExtractionError(LegalAIException):
    """Raised when citation extraction fails"""

    def __init__(
        self,
        message: str = "Citation extraction error",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ConversationNotFoundError(LegalAIException):
    """Raised when conversation is not found"""

    def __init__(
        self,
        message: str = "Conversation not found",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class AuthenticationError(LegalAIException):
    """Raised when authentication fails"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(LegalAIException):
    """Raised when authorization fails"""

    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


# ============================================================================
# Exception Handlers for FastAPI
# ============================================================================


async def legal_ai_exception_handler(
    request: Request,
    exc: LegalAIException
) -> JSONResponse:
    """
    Handle all Legal AI custom exceptions

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": type(exc).__name__,
                "message": exc.message,
                "details": exc.details,
                "path": str(request.url.path),
            }
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle all unhandled exceptions

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": {
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
                "path": str(request.url.path),
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle Pydantic validation exceptions

    Args:
        request: FastAPI request object
        exc: Pydantic ValidationError

    Returns:
        JSON response with validation error details
    """
    # This will be called for RequestValidationError from FastAPI
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": {
                    "errors": str(exc),
                },
                "path": str(request.url.path),
            }
        }
    )


# ============================================================================
# Helper Functions
# ============================================================================


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI app

    Args:
        app: FastAPI application instance
    """
    from fastapi.exceptions import RequestValidationError

    # Register custom exception handlers
    app.add_exception_handler(LegalAIException, legal_ai_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)


def raise_if_error(
    condition: bool,
    exception_class: type[LegalAIException],
    message: str,
    details: Optional[dict[str, Any]] = None
) -> None:
    """
    Raise exception if condition is True

    Args:
        condition: Condition to check
        exception_class: Exception class to raise
        message: Error message
        details: Additional error details

    Raises:
        exception_class: If condition is True
    """
    if condition:
        raise exception_class(message=message, details=details)


def raise_if_not(
    condition: bool,
    exception_class: type[LegalAIException],
    message: str,
    details: Optional[dict[str, Any]] = None
) -> None:
    """
    Raise exception if condition is False

    Args:
        condition: Condition to check
        exception_class: Exception class to raise
        message: Error message
        details: Additional error details

    Raises:
        exception_class: If condition is False
    """
    if not condition:
        raise exception_class(message=message, details=details)
