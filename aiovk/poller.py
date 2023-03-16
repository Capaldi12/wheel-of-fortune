"""Poller for long polling."""
from functools import partial
from traceback import print_exc
from typing import Callable, Optional, Any
from asyncio import Task, create_task

from aiohttp import ClientSession


class Poller:
    """Polls long poll server and passes updates to callback function"""

    class Failed(Exception):
        """Polling request has failed."""

        code: int
        ts: Optional[int]

        def __init__(self, code: int, ts: int = None):
            super().__init__()

            self.code = code
            self.ts = ts

        def __str__(self):
            return f'(failed: {self.code}, ts: {self.ts})'

        def __repr__(self):
            return f'{self.__class__.__name__}{self}'

    callbacks: dict[str, Callable]
    error_handler: Callable
    fail_handler: Callable

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

        self.callbacks = {'': self._no_op}
        self.error_handler = self._error_handler
        self.fail_handler = self._fail_handler

    @staticmethod
    async def _no_op(*_, **__):
        pass

    @staticmethod
    async def _error_handler(exception):
        print('Error in Poller:')
        print_exc()
        return True

    async def _fail_handler(self, fail: Failed):
        # Ignores other types of fail, since there's no way to call api
        if fail.code == 1:
            self.ts = fail.ts

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

            try:
                updates = await self._get_updates()

            except Poller.Failed as fail:
                await self.fail_handler(fail)

            else:
                for update in updates:
                    await self._handle(update)

    async def _get_updates(self) -> list[dict]:
        """Perform long poll request."""

        async with self.session.get(self.server, params=self.params) as resp:
            data = await resp.json()

        if 'failed' in data:
            raise Poller.Failed(data['failed'], data.get('ts'))

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
                await self._error_handler(e)

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

        self.callbacks[update_type] = self._no_op
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

    def on_fail(self, handler: Callable):
        """
        Set handler for polling fail.

        Handler should be used to repeat groups.getLongPollServer call and
        update server, key and/or ts values. Handler will get Poller.Failed
        object, containing code of fail (and ts, if it was returned).

        code:
            1 - event history is outdated or partially lost, use ts provided
            2 - key expired, request new one using groups.getLongPollServer
            3 - information lost, request new key and server using
                groups.getLongPollServer

        :param handler: New failure handler.
        :return: This poller for chaining.
        """

        self.fail_handler = handler
        return self

    async def dispose(self):
        """Stop polling if running and dispose of session if it was created."""

        if self.running:
            await self.stop_polling()

        if self._owns_session and self.session:
            await self.session.close()
