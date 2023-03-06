"""Random useful functions."""
__all__ = ['json_response', 'error_json_response', 'snakeify']

from typing import Any, Optional
import re

from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web import Response


def json_response(data: Any = None, status: str = "ok") -> Response:
    """
    Return JSON response with given data.

    :param data: Data to be returned.
    :param status: Status message.
    :return: JSON response.
    """

    if data is None:
        data = {}

    return aiohttp_json_response(
        data={
            "status": status,
            "data": data,
        }
    )


def error_json_response(
    http_status: int,
    status: str = "error",
    message: Optional[str] = None,
    data: Optional[dict] = None,
):
    """
    Return JSON response with given error info.

    :param http_status: Status code.
    :param status: Status text.
    :param message: Message about the error.
    :param data: Error details.
    :return: JSON response.
    """

    if data is None:
        data = {}

    if message is None:
        message = status

    return aiohttp_json_response(
        data={
            "status": status,
            "message": message,
            "data": data,
        },
        status=http_status
    )


def snakeify(name: str) -> str:
    """
    Turn CamelCase name into a snake_case one.

    :param name: Name to transform.
    :return: Transformed name.
    """

    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
