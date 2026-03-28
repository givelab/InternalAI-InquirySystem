import logging

from fastapi import Request

from src.utils.logs import LogClient

logger = logging.getLogger(__name__)


def get_logger(request: Request) -> LogClient:
    log_client = LogClient(trace_id=request.state.trace_id)
    return log_client
