"""Base class for data accessors."""
__all__ = ['Accessor']

import typing
import logging

if typing.TYPE_CHECKING:
    from ..application import Application


class Accessor:
    """Base class for data accessors."""
    app: 'Application'

    logger: logging.Logger

    def __init__(self, app: 'Application', name: str = None):
        self.app = app

        app.on_startup.append(self.startup)
        app.on_cleanup.insert(0, self.cleanup)  # lifo

        self.logger = logging.getLogger(
            f'app.store.{name or self.__class__.__name__}')

    async def startup(self, app: 'Application'):
        pass    # pragma: no cover

    async def cleanup(self, app: 'Application'):
        pass    # pragma: no cover
