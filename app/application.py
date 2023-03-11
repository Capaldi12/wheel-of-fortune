"""Core classes for the application."""
__all__ = ['Application', 'Request', 'View']

import typing
from typing import Optional

from aiohttp.web import Application as AiohttpApplication, \
    Request as AiohttpRequest, View as AiohttpView

from .config import Config

# Prevent circular imports
if typing.TYPE_CHECKING:
    from .database import Database
    from .store import Store
    from .admin.models import Admin


class Application(AiohttpApplication):
    """The main application class."""
    config: Config
    database: 'Database'
    store: 'Store'

    def __init__(self, config_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = Config.from_yaml(config_path)


class Request(AiohttpRequest):
    """Replaces requests received by the application."""
    app: Application


class View(AiohttpView):
    """Base class for views."""

    request: Request

    @property
    def app(self) -> Application:
        """App the view belongs to."""
        return self.request.app

    @property
    def data(self) -> dict:
        """Request data parsed by aiohttp_apispec."""
        return self.request.get('data', {})

    @property
    def admin(self) -> Optional['Admin']:
        """Admin object from the request session."""
        return self.request.get('admin', None)
