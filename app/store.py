"""Store class for the application. Contains all the accessors."""
__all__ = ['Store']

import typing

from .admin import AdminAccessor
from .game import GameAccessor
from .bot import BotAccessor

if typing.TYPE_CHECKING:
    from .application import Application


class Store:
    """Store class for the application. Contains all the accessors."""

    admins: AdminAccessor
    game: GameAccessor
    bot: BotAccessor

    def __init__(self, app: 'Application'):
        self.admins = AdminAccessor(app, 'admins')
        self.game = GameAccessor(app, 'game')
        self.bot = BotAccessor(app, 'bot')
