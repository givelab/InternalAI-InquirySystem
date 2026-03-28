from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.utils.exceptions import (
    ModelValidationError,
    RecordAlreadyExistsError,
    RecordNotFoundError,
)
from src.utils.logs import LogClient


def generate_json_response_from_pydantic_validation_error(
    default_status_code: int,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=default_status_code,
        content=jsonable_encoder(
            {
                "messages": [
                    {"type": e["type"], "loc": e["loc"], "msg": e["msg"]} for e in exc.errors()
                ]
            }
        ),
    )


def generate_json_response_with_exception(
    request: Request, status_code: int, exc: Exception
) -> JSONResponse:
    logger = LogClient(trace_id=request.state.trace_id)
    log_message = f"{request.method} {request.url.path} error: {exc}"
    if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(log_message)
    else:
        logger.info(log_message)

    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY and isinstance(
        exc, RequestValidationError
    ):
        return generate_json_response_from_pydantic_validation_error(status_code, exc)

    if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        exc.args = ("internal server error",)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"messages": exc.args}),
    )


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ModelValidationError)
    def model_validation_error_handler(
        request: Request,
        exc: ModelValidationError,
    ) -> JSONResponse:
        return generate_json_response_with_exception(request, status.HTTP_400_BAD_REQUEST, exc)

    @app.exception_handler(RecordNotFoundError)
    def record_not_found_error_handler(
        request: Request,
        exc: RecordNotFoundError,
    ) -> JSONResponse:
        return generate_json_response_with_exception(request, status.HTTP_404_NOT_FOUND, exc)

    @app.exception_handler(RecordAlreadyExistsError)
    def record_already_exists_error_handler(
        request: Request,
        exc: RecordAlreadyExistsError,
    ) -> JSONResponse:
        return generate_json_response_with_exception(request, status.HTTP_409_CONFLICT, exc)

    @app.exception_handler(RequestValidationError)
    def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return generate_json_response_with_exception(
            request, status.HTTP_422_UNPROCESSABLE_ENTITY, exc
        )

    @app.exception_handler(Exception)
    def internal_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return generate_json_response_with_exception(
            request, status.HTTP_500_INTERNAL_SERVER_ERROR, exc
        )
