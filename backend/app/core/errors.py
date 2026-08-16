import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class TradeWiseException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(TradeWiseException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None, code: str = "NOT_FOUND"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedError(TradeWiseException):
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None, code: str = "UNAUTHORIZED"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(TradeWiseException):
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None, code: str = "FORBIDDEN"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictError(TradeWiseException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None, code: str = "CONFLICT"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class InsufficientFundsError(TradeWiseException):
    def __init__(self, message: str = "Insufficient cash balance for this trade", details: Optional[Dict[str, Any]] = None, code: str = "INSUFFICIENT_CASH"):
        super().__init__(
            message=message,
            code=code,
            status_code=422,
            details=details,
        )


class ServiceUnavailableError(TradeWiseException):
    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[Dict[str, Any]] = None, code: str = "SERVICE_UNAVAILABLE"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(TradeWiseException)
    async def tradewise_exception_handler(request: Request, exc: TradeWiseException) -> JSONResponse:
        logger.warning(
            f"TradeWiseException: {exc.code} - {exc.message}",
            extra={"error_code": exc.code, "details": exc.details, "path": request.url.path},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        logger.info(
            f"Validation error on {request.url.path}: {errors}",
            extra={"validation_errors": errors, "path": request.url.path},
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request payload failed validation.",
                    "details": {"errors": errors},
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning(
            f"HTTPException: {exc.status_code} - {exc.detail}",
            extra={"status_code": exc.status_code, "path": request.url.path},
        )
        code = "HTTP_ERROR"
        if exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 409:
            code = "CONFLICT"

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            f"Unhandled exception on {request.url.path}: {str(exc)}",
            exc_info=True,
            extra={"path": request.url.path},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                    "details": {},
                }
            },
        )
