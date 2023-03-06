"""Authentication middleware."""
__all__ = ['auth_middleware', 'auth_required']

from aiohttp.web import View
from aiohttp.web_exceptions import HTTPUnauthorized
from aiohttp.web import middleware
from aiohttp_session import get_session

from ..application import Request


@middleware
async def auth_middleware(request: Request, handler: callable):
    """Authentication middleware."""

    session = await get_session(request)

    if session:
        request['admin'] = session.get('admin')

    if _requires_auth(request):
        if request.get('admin') is None:
            raise HTTPUnauthorized

    return await handler(request)


def auth_required(method):
    """Mark method as requiring authentication."""

    if not hasattr(method, '__auth__'):
        method.__auth__ = True

    return method


def _requires_auth(request: Request) -> bool:
    """Check if method for given request requires authentication."""

    orig_handler = request.match_info.handler

    if hasattr(orig_handler, '__auth__'):
        return orig_handler.__auth__

    if _issubclass(orig_handler, View):
        sub_handler = getattr(orig_handler, request.method.lower(), None)
        return getattr(sub_handler, '__auth__', False)

    return False


def _issubclass(cls, cls_info):
    """Fix for when one of the classes is not a type (for some reason)."""

    try:
        return issubclass(cls, cls_info)
    except TypeError:
        return False
