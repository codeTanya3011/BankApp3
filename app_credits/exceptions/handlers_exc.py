from fastapi import Request, status
from fastapi.responses import JSONResponse
from .base_exc import AppException
from .not_found import NotFoundUserError
from sqlalchemy.exc import IntegrityError


def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "type": exc.__class__.__name__
        }
    )


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "InternalError"
        }
    )


def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc.orig),
            "type": "IntegrityError"
        }
    )


def not_found_user_error_handler(request: Request, exc: NotFoundUserError):
    return JSONResponse(
        status_code=404,
        content={
            "type": "NotFoundUserError",
            "message": exc.message,
            "user_id": exc.user_id
        }
    )