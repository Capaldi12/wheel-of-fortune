"""Poller for long polling."""
from functools import partial
from traceback import print_exc
from typing import Callable, Optional, Any
from asyncio import Task, create_task

from aiohttp import ClientSession


class Poller:
    """Polls long poll server and passes updates to callback function"""

    callbacks: dict[str, Callable]
    error_handler: Callable

    def __init__(self, server: str, key: str, ts: int = 1, wait: int = 25,
                 session: Optional[ClientSession] = None):

        self.server = server
        self.key = key
        self.ts = ts

        self.wait = wait

        self._owns_session = session is None
        if session:
            self.session = session
        else:
            self.session = ClientSession()

        self.running = False
        self.task: Optional[Task] = None

        self.callbacks = {'': self.__no_op}
        self.error_handler = self.__handler

    @staticmethod
    async def __no_op(*_, **__):
        pass

    @staticmethod
    async def __handler(exception):
        print_exc()
        return True

    @property
    def params(self) -> dict[str, Any]:
        """Parameters for long poll request."""

        return {
            'act': 'a_check',
            'key': self.key,
            'ts': self.ts,
            'wait': self.wait
        }

    async def start_polling(self):
        """Start polling of long poll server."""

        if not self.running:
            self.running = True
            self.task = create_task(self._poll())

    async def stop_polling(self):
        """Stop polling of long poll server."""

        if self.running:
            self.running = False
            self.task.cancel()

    async def _poll(self):
        """Polling loop."""

        while self.running:
            updates = await self._get_updates()
            for update in updates:
                await self._handle(update)

    async def _get_updates(self) -> list[dict]:
        """Perform long poll request."""

        async with self.session.get(self.server, params=self.params) as resp:
            data = await resp.json()

        self.ts = data['ts']
        return data['updates']

    async def _handle(self, update):
        """Handle an update."""

        try:
            type_ = update['type']
            update = self._prepare_update(update)

            if type_ in self.callbacks:
                await self.callbacks[type_](update)
            else:
                await self.callbacks[''](update)

        except Exception as e:
            if not await self.error_handler(e):
                await self.__handler(e)

    def _prepare_update(self, update: dict) -> Any:
        """Place to add extra data or convert to data type."""
        return update

    def on(self, update_type: str, callback: Callable, **kwargs):
        """
        Register callback function for given update type.

        :param update_type: Type of the update.
        :param callback: Callback function.
        :param kwargs: Extra arguments for callback function.
        :return: This poller for chaining.
        """

        if kwargs:
            callback = partial(callback, **kwargs)

        self.callbacks[update_type] = callback
        return self

    def default(self, callback: Callable, **kwargs):
        """
        Set default callback function.

        :param callback: Callback function.
        :param kwargs: Extra arguments for callback function.
        :return: This poller for chaining.
        """

        if kwargs:
            callback = partial(callback, **kwargs)

        self.callbacks[''] = callback
        return self

    def ignore(self, update_type: str):
        """
        Ignore specified update type (don't pass it even to fallback).

        :param update_type: Update type to ignore.
        :return: This poller for chaining.
        """

        self.callbacks[update_type] = self.__no_op
        return self

    def on_error(self, handler: Callable):
        """
        Set error handler.

        Handler should return True if error is handled. If False is returned,
        error will be handled by default handler.

        Don't raise exceptions in handler - they will just kill polling task
        without any indication.

        :param handler: New error handler.
        :return: This poller for chaining.
        """

        self.error_handler = handler
        return self

    async def dispose(self):
        """Stop polling if running and dispose of session if it was created."""

        if self.running:
            await self.stop_polling()

        if self._owns_session and self.session:
            await self.session.close()
