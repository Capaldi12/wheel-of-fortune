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

    def __init__(self, vk: "VK", server: str, key: str, ts: int = 1,
                 wait: int = 25, session: Optional[ClientSession] = None):
        super().__init__(server, key, ts, wait, session)
        self.vk = vk

    def _prepare_update(self, update: dict) -> Any:
        match update['type']:
            case 'message_new':
                return Message(self.vk, update['object']['message'],
                               update['object']['client_info'])
            case 'message_event':
                return MessageEvent(self.vk, update['object'])

        return update
