import re
from typing import Any

from src.utils.exceptions import ModelValidationError


def validate_not_none(key: str, value: Any | None) -> None:
    if value is None:
        raise ModelValidationError(f"{key} is required")
    return None


def validate_string_length(
    key: str, value: str | None, min_length: int | None, max_length: int | None
) -> None:
    if value is None:
        raise ModelValidationError(f"{key} is required")
    if min_length is not None and len(value) < min_length:
        raise ModelValidationError(f"{key} is too short")
    if max_length is not None and len(value) > max_length:
        raise ModelValidationError(f"{key} is too long")
    return None


def validate_email(key: str, value: str | None) -> None:
    if value is None:
        raise ModelValidationError(f"{key} is required")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
        raise ModelValidationError(f"{key} is not a valid email")
    return None
