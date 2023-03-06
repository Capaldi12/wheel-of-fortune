"""Wheel of fortune VK bot."""
__all__ = ['setup_app']

from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp_apispec import validation_middleware

# Core
from .application import Application
from .config import Config
from .database import Database
from .store import Store

# Middleware
from .middlewares import error_handling_middleware, auth_middleware

# Modules
from . import admin


def setup_app(config_path):
    """Create and configure an aiohttp application."""

    app = Application(config_path)

    app.middlewares.extend([
        error_handling_middleware,
        session_middleware(EncryptedCookieStorage(app.config.session.key)),
        auth_middleware,
        validation_middleware,
    ])

    app.database = Database(app)
    app.store = Store(app)

    app.add_routes(admin.routes)

    setup_aiohttp_apispec(
        app, title="Wheel Of Fortune Bot",
        url="/docs/json", swagger_path="/docs"
    )

    return app
