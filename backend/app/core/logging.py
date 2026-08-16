import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import json as jsonlogger

# Context variable for request ID propagation across async tasks
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get() or "-"
        return True


def setup_logging(log_level: str = "INFO") -> None:
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    log_handler.setFormatter(formatter)
    log_handler.addFilter(RequestIDFilter())
    logger.addHandler(log_handler)

    # Tone down noisy loggers
    logging.getLogger("uvicorn.access").handlers = [log_handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx_var.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx_var.reset(token)
