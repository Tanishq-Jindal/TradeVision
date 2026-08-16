import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class TradeVisionException(Exception):
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


# Backward compatibility alias
TradeWiseException = TradeVisionException


class NotFoundError(TradeVisionException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None, code: str = "NOT_FOUND"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedError(TradeVisionException):
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None, code: str = "UNAUTHORIZED"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(TradeVisionException):
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None, code: str = "FORBIDDEN"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictError(TradeVisionException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None, code: str = "CONFLICT"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class InsufficientFundsError(TradeVisionException):
    def __init__(self, message: str = "Insufficient cash balance for this trade", details: Optional[Dict[str, Any]] = None, code: str = "INSUFFICIENT_CASH"):
        super().__init__(
            message=message,
            code=code,
            status_code=422,
            details=details,
        )


class ServiceUnavailableError(TradeVisionException):
    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[Dict[str, Any]] = None, code: str = "SERVICE_UNAVAILABLE"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(TradeVisionException)
    async def tradevision_exception_handler(request: Request, exc: TradeVisionException) -> JSONResponse:
        logger.warning(
            f"TradeVisionException: {exc.code} - {exc.message}",
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
        details = {}
        for err in errors:
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            details[loc] = err.get("msg", "Invalid value")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request payload failed schema validation.",
                    "details": details,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            404: "NOT_FOUND",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            405: "METHOD_NOT_ALLOWED",
            500: "INTERNAL_SERVER_ERROR",
        }
        err_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": err_code,
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            f"Unhandled server error on {request.url.path}: {str(exc)}",
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
