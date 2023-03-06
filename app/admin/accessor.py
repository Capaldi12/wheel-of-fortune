"""Admin accessor."""
__all__ = ['AdminAccessor']

import typing
from typing import Optional

from sqlalchemy import select, Result
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..base import Accessor
from .models import Admin

if typing.TYPE_CHECKING:
    from ..application import Application


class AdminAccessor(Accessor):
    """Admin accessor. Contains logic for working with admin model."""

    async def startup(self, app: 'Application'):
        if not await self.get_by_email(app.config.admin.email):
            print('Creating admin from config')
            await self.create(app.config.admin.email, app.config.admin.password)

    async def get_by_id(self, id_: int) -> Optional[Admin]:
        """
        Get admin with specified id.

        :param id_: id of the admin.
        :return: Admin or None if it does not exist.
        """

        async with self._session() as session:
            result = await session.execute(
                select(Admin).where(Admin.id == id_))

            return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Admin]:
        """
        Get admin with specified email.

        :param email: email of the admin.
        :return: Admin or None if it does not exist.
        """

        async with self._session() as session:
            result: Result = await session.execute(
                select(Admin).where(Admin.email == email))

            return result.scalar_one_or_none()

    async def create(self, email: str, password: str) -> Admin:
        """
        Create new admin.

        :param email: Email address.
        :param password: Password to set.
        :return: Created admin.
        """

        async with self._session.begin() as session:
            admin = Admin(email=email, password=password)
            session.add(admin)

        return admin

    @property
    def _session(self) -> async_sessionmaker:
        return self.app.database.session
