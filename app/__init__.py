"""Wheel of fortune VK bot."""
__all__ = ['setup_app']

import logging

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
from . import game


def setup_app(config_path):
    """Create and configure an aiohttp application."""

    app = Application(config_path,
                      handler_args={'access_log_format': '%r %s %b'})

    logging.basicConfig(
        level=getattr(logging, app.config.log_level.upper(), logging.INFO),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%y.%m.%d %H:%M:%S',

    )

    app.middlewares.extend([
        error_handling_middleware,
        session_middleware(EncryptedCookieStorage(app.config.session.key)),
        auth_middleware,
        validation_middleware,
    ])

    app.database = Database(app)
    app.store = Store(app)

    app.add_routes(admin.routes)
    app.add_routes(game.routes)

    setup_aiohttp_apispec(
        app, title="Wheel Of Fortune Bot",
        url="/docs/json", swagger_path="/docs"
    )

    return app
