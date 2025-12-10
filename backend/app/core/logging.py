"""
Logging configuration and utilities with structured logging support
"""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional

from pythonjsonlogger import jsonlogger

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any]
    ) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add log level
        log_record["level"] = record.levelname

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_record["request_id"] = request_id

        # Add logger name
        log_record["logger"] = record.name

        # Add module and function info
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)


class PrettyFormatter(logging.Formatter):
    """Pretty formatter for development with colors"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",      # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        colored_level = f"{level_color}{record.levelname:8}{self.COLORS['RESET']}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Get request ID if available
        request_id = request_id_var.get()
        request_id_str = f"[{request_id[:8]}]" if request_id else "[--------]"

        # Build message
        message = record.getMessage()

        # Add extra fields if present
        extra_str = ""
        if hasattr(record, "extra_fields") and record.extra_fields:
            extra_str = f" | {json.dumps(record.extra_fields)}"

        # Format: timestamp [request_id] LEVEL module.function:line - message [extra]
        log_line = (
            f"{timestamp} {request_id_str} "
            f"{colored_level} "
            f"{record.name}.{record.funcName}:{record.lineno} - "
            f"{message}"
            f"{extra_str}"
        )

        # Add exception info if present
        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


def setup_logging(log_level: str = "INFO", environment: str = "dev") -> None:
    """
    Setup application logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment (dev, staging, prod)
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Use JSON formatter for production, pretty formatter for development
    if environment == "prod":
        formatter = JSONFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = PrettyFormatter()

    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)

    # Set log level for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: str) -> None:
    """
    Set request ID for current context

    Args:
        request_id: Request ID to set
    """
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """
    Get request ID from current context

    Returns:
        Current request ID or None
    """
    return request_id_var.get()


def log_with_extra(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_fields: Any
) -> None:
    """
    Log message with extra fields

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **extra_fields: Additional fields to include in log
    """
    log_method = getattr(logger, level.lower())
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "(unknown file)",
        0,
        message,
        (),
        None
    )
    record.extra_fields = extra_fields
    logger.handle(record)


# Example usage functions
def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float
) -> None:
    """
    Log API request

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    log_with_extra(
        logger,
        "info",
        f"{method} {path} - {status_code}",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2)
    )


def log_llm_request(
    logger: logging.Logger,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: float
) -> None:
    """
    Log LLM request

    Args:
        logger: Logger instance
        provider: LLM provider (gemini, claude)
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        duration_ms: Request duration in milliseconds
    """
    log_with_extra(
        logger,
        "info",
        f"LLM request to {provider} ({model})",
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        duration_ms=round(duration_ms, 2)
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict[str, Any]] = None
) -> None:
    """
    Log error with context

    Args:
        logger: Logger instance
        error: Exception instance
        context: Additional context information
    """
    extra_fields = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if context:
        extra_fields["context"] = context

    log_with_extra(
        logger,
        "error",
        f"Error occurred: {error}",
        **extra_fields
    )
