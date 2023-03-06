"""Error handling middleware."""
__all__ = ['error_handling_middleware']

import json
from traceback import format_exc

from aiohttp.web_exceptions import HTTPUnprocessableEntity, HTTPException
from aiohttp.web import middleware

from ..application import Request
from ..util import error_json_response, snakeify


@middleware
async def error_handling_middleware(request: "Request", handler):
    """Error handling middleware. Ensures that all responses are in JSON."""

    try:
        return await handler(request)

    except HTTPUnprocessableEntity as e:
        # Validation errors
        return error_json_response(
            http_status=e.status,
            status='unprocessable_entity',
            message=e.reason,
            data=json.loads(e.text),  # Contains info about why data is invalid
        )
    except HTTPException as e:
        # General http errors
        return error_json_response(
            http_status=e.status,
            status=snakeify(e.__class__.__name__.replace('HTTP', '')),
            message=e.reason,
        )
    except Exception:
        # Any other errors
        return error_json_response(
            http_status=500,
            status='internal_server_error',
            message=format_exc(),
        )
