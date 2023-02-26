"""Poller for long polling."""
from functools import partial
from traceback import print_exc
from typing import Callable, Optional, Any
from asyncio import Task, create_task

from aiohttp import ClientSession


class Poller:
    """Polls long poll server and passes updates to callback function"""

    callbacks: dict[str, Callable]

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

    async def __no_op(*_, **__):
        pass

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
            self.task = create_task(self.poll())

    async def stop_polling(self):
        """Stop polling of long poll server."""

        if self.running:
            self.running = False
            await self.task

    async def poll(self):
        """Polling loop."""

        while self.running:
            updates = await self.get_updates()
            for update in updates:
                await self.handle(update)

    async def get_updates(self) -> list[dict]:
        """Perform long poll request."""

        async with self.session.get(self.server, params=self.params) as resp:
            data = await resp.json()

        self.ts = data['ts']
        return data['updates']

    async def handle(self, update):
        """Handle an update."""

        try:
            type_ = update['type']
            if type_ in self.callbacks:
                await self.callbacks[type_](update)
            else:
                await self.callbacks[''](update)

        except:  # Logging purposes
            print_exc()

    def on(self, update_type: str, callback: Callable, **kwargs):
        """
        Register callback function for given update type.

        :param update_type: Type of the update.
        :param callback: Callback function.
        :param kwargs: Extra arguments for callback function.
        :return: This poller for chaining.
        """

        self.callbacks[update_type] = partial(callback, **kwargs)
        return self

    def default(self, callback: Callable, **kwargs):
        """
        Set default callback function.

        :param callback: Callback function.
        :param kwargs: Extra arguments for callback function.
        :return: This poller for chaining.
        """

        self.callbacks[''] = partial(callback, **kwargs)
        return self

    def ignore(self, update_type: str):
        """
        Ignore specified update type (don't pass it even to fallback).

        :param update_type: Update type to ignore.
        :return: This poller for chaining.
        """

        self.callbacks[update_type] = self.__no_op
        return self

    async def dispose(self):
        """Stop polling if running and dispose of session if it was created."""

        if self.running:
            await self.stop_polling()

        if self._owns_session and self.session:
            await self.session.close()
