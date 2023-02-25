"""Poller for long polling."""
from functools import partial
from typing import Callable, Optional, Any
from asyncio import Task, create_task

from aiohttp import ClientSession


class Poller:
    """Polls long poll server and passes updates to callback function"""

    callback: Callable

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

    @property
    def params(self) -> dict[str, Any]:
        """Parameters for long poll request."""

        return {
            'act': 'a_check',
            'key': self.key,
            'ts': self.ts,
            'wait': self.wait
        }

    async def start_polling(self, new_callback: Optional[Callable] = None,
                            *args, **kwargs):
        """
        Start polling of long poll server.
        Assign new callback to callback if provided.
        All additional arguments and keyword arguments
        will be passed to new_callback on call.
        Make sure new_callback can accept updates list.

        :param new_callback: new callback to set.
        :param args: arguments to new callback.
        :param kwargs: keyword arguments to new callback.
        """
        if new_callback:
            self.callback = partial(new_callback, *args, **kwargs)

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
            await self.callback(updates)

    async def get_updates(self) -> list[dict]:
        """Perform long poll request."""

        async with self.session.get(self.server, params=self.params) as resp:
            data = await resp.json()

        self.ts = data['ts']
        return data['updates']

    async def dispose(self):
        """Stop polling if running and dispose of session if it was created."""

        if self.running:
            await self.stop_polling()

        if self._owns_session and self.session:
            await self.session.close()
