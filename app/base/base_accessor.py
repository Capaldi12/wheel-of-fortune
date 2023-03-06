"""Base class for data accessors."""
__all__ = ['Accessor']

import typing

if typing.TYPE_CHECKING:
    from ..application import Application


class Accessor:
    """Base class for data accessors."""
    app: 'Application'

    def __init__(self, app: 'Application'):
        self.app = app

        app.on_startup.append(self.startup)
        app.on_cleanup.insert(0, self.cleanup)  # lifo

    async def startup(self, app: 'Application'):
        pass    # pragma: no cover

    async def cleanup(self, app: 'Application'):
        pass    # pragma: no cover
