"""
Core module exports
"""
from .config import Settings, get_settings
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    CitationExtractionError,
    ConfigurationError,
    ConversationNotFoundError,
    LegalAIException,
    LLMError,
    RateLimitError,
    TaxCodeNotFoundError,
    ValidationError,
    VectorDBError,
    register_exception_handlers,
    raise_if_error,
    raise_if_not,
)
from .logging import (
    get_logger,
    get_request_id,
    log_api_request,
    log_error,
    log_llm_request,
    log_with_extra,
    set_request_id,
    setup_logging,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Exceptions
    "LegalAIException",
    "TaxCodeNotFoundError",
    "LLMError",
    "RateLimitError",
    "ValidationError",
    "ConfigurationError",
    "VectorDBError",
    "CitationExtractionError",
    "ConversationNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "register_exception_handlers",
    "raise_if_error",
    "raise_if_not",
    # Logging
    "setup_logging",
    "get_logger",
    "set_request_id",
    "get_request_id",
    "log_with_extra",
    "log_api_request",
    "log_llm_request",
    "log_error",
]
