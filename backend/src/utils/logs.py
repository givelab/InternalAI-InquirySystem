import json
import logging
import typing
from datetime import datetime

import uuid6
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.settings import settings

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


def set_basic_config() -> None:
    logging.basicConfig(format="%(message)s", level=settings.log_level.upper())


class LogClient:
    def __init__(self, trace_id: str | None = None) -> None:
        self.logger = logging.getLogger("BackendLogger")
        self.trace_id = (
            trace_id  # 識別子をログに含めることで、リクエストのログを追跡できるようにする
        )

    def build_log_message(self, message: str, level: str) -> str:
        return json.dumps(
            {
                "source": self.logger.name,
                "level": level,
                "timestamp": datetime.utcnow().isoformat(sep="T", timespec="microseconds") + "Z",
                "trace_id": self.trace_id,
                "message": message,
            }
        )

    def debug(self, message: str) -> None:
        self.logger.debug(self.build_log_message(message, logging.getLevelName(logging.DEBUG)))

    def info(self, message: str) -> None:
        self.logger.info(self.build_log_message(message, logging.getLevelName(logging.INFO)))

    def warning(self, message: str) -> None:
        self.logger.warning(self.build_log_message(message, logging.getLevelName(logging.WARNING)))

    def error(self, message: str) -> None:
        self.logger.error(self.build_log_message(message, logging.getLevelName(logging.ERROR)))

    def critical(self, message: str) -> None:
        self.logger.critical(
            self.build_log_message(message, logging.getLevelName(logging.CRITICAL))
        )


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # リクエストごとに一意な識別子を生成し、リクエストごとのログを追跡できるようにする
        # request.stateの使い方については以下を参照
        # https://fastapi.tiangolo.com/tutorial/sql-databases/#about-requeststate
        trace_id = str(uuid6.uuid7())
        request.state.trace_id = trace_id

        response = await call_next(request)

        LogClient(trace_id=trace_id).info(
            f"Request: {request.method} {request.url._url} Response: {response.status_code}"
        )

        return response
