"""Poller for long polling."""

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

        if session:
            self.session = session
        else:
            self.session = ClientSession()

        self.running = False
        self.task: Optional[Task] = None

    @property
    def params(self) -> dict[str, Any]:
        return {
            'act': 'a_check',
            'key': self.key,
            'ts': self.ts,
            'wait': self.wait
        }

    async def start_polling(self, new_callback: Optional[Callable] = None):
        if new_callback:
            self.callback = new_callback

        if not self.running:
            self.running = True
            self.task = create_task(self.poll())

    async def stop_polling(self):
        if self.running:
            self.running = False
            await self.task

    async def poll(self):
        while self.running:
            updates = await self.get_updates()
            await self.callback(updates)

    async def get_updates(self) -> list[dict]:
        async with self.session.get(self.server, params=self.params) as resp:
            data = await resp.json()

        self.ts = data['ts']
        return data['updates']

    async def dispose(self):
        await self.session.close()
