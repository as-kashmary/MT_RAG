import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

from pythonjsonlogger import jsonlogger

# -------------------------------------------------------------------
# Context variable (per-request)
# -------------------------------------------------------------------
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar(
    "request_id", default=None
)


def get_request_id() -> Optional[str]:
    return request_id_ctx_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    rid = request_id or str(uuid.uuid4())
    request_id_ctx_var.set(rid)
    return rid


# -------------------------------------------------------------------
# Custom JSON Formatter
# -------------------------------------------------------------------
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["request_id"] = get_request_id()

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


# -------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------
def configure_logging(
    level: str = "INFO",
    service_name: str = "fastapi-app",
) -> None:
    """
    Configure logging for production FastAPI apps.
    Call this ONCE on startup.
    """

    log_level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        "%(asctime)s %(level)s %(name)s %(message)s",
        rename_fields={
            "asctime": "timestamp",
            "message": "message",
        },
    )
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    root_logger.addHandler(handler)

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    root_logger.info(
        "Logging configured",
        extra={
            "service": service_name,
            "log_level": level,
        },
    )


# -------------------------------------------------------------------
# Logger factory
# -------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
