"""Database class, responsible for connecting to the database."""
__all__ = ['Database']

import typing
from typing import Type

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, \
    create_async_engine, async_sessionmaker

from ..base import Accessor
from .declarative_base import Base

if typing.TYPE_CHECKING:
    from ..application import Application


class Database(Accessor):
    """Database class, responsible for connecting to the database."""

    _engine: AsyncEngine
    _base: Type[DeclarativeBase]
    session: async_sessionmaker[AsyncSession]  # Session factory for general use

    def __init__(self, app: 'Application'):
        super().__init__(app)

        self._base = Base

    async def startup(self, app: 'Application'):
        self._engine = create_async_engine(
            app.config.database.url, echo=app.config.database.echo
        )

        self.session = async_sessionmaker(self._engine, expire_on_commit=False)

    async def cleanup(self, app: 'Application'):
        if self._engine:
            await self._engine.dispose()
