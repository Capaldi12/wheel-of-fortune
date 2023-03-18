"""Annotated version of Poller class."""
__all__ = ['Poller']

import typing
from typing import Any, Optional

from aiohttp import ClientSession

from ..poller import Poller as BasePoller
from .message import Message, MessageEvent

if typing.TYPE_CHECKING:
    from .vk import VK


class Poller(BasePoller):
    """Annotated version of Poller class."""

    def __init__(self, vk: "VK", group_id: int,
                 server: str, key: str, ts: int = 1,
                 wait: int = 25, session: Optional[ClientSession] = None):
        super().__init__(server, key, ts, wait, session)
        self.vk = vk
        self.group_id = group_id

    async def _fail_handler(self, fail: BasePoller.Failed):
        self.logger.info(f'Polling failed: {fail.reason}')

        if fail.code == 1:
            self.ts = fail.ts
            return

        self.logger.info('Request new poller')
        poller = await self.vk.groups.getLongPollServer(group_id=self.group_id)

        self.key = poller.key

        if fail.code == 3:
            self.server = poller.server

        await poller.dispose()
        self.logger.info('Resume polling')

    def _prepare_update(self, update: dict) -> Any:
        match update['type']:
            case 'message_new':
                return Message(self.vk, update['object']['message'],
                               update['object']['client_info'])
            case 'message_event':
                return MessageEvent(self.vk, update['object'])

        return update
