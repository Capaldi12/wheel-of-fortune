"""Dataclasses for message events."""
__all__ = ['Message', 'ClientInfo', 'MessageEvent']

import json
from pprint import pformat

import typing
from typing import Any, Optional

if typing.TYPE_CHECKING:
    from .vk import VK


class ClientInfo:
    """Represents information about the client."""

    def __init__(self, client_info: Optional[dict[str, Any]]):
        self.client_info = client_info or {}

    def __getattr__(self, item: str):
        if item in self.client_info:
            return self.client_info[item]

        raise AttributeError(f'There is no {item} in this '
                             f'{self.__class__.__name__}.')

    def __contains__(self, item: str) -> bool:
        return item in self.client_info

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(' \
               f'{pformat(self.client_info, sort_dicts=False)})'


class Message:
    """Message received from VK API."""

    @property
    def is_private(self) -> bool:
        """Whether message was sent in private dialog."""

        return self.peer_id < 2e9

    def __init__(self, vk: "VK", message: dict[str, Any],
                 client_info: Optional[dict[str, Any]] = None):

        self.vk = vk
        self.message = message
        self.client_info = ClientInfo(client_info)

        if 'payload' in self.message:
            self.message['payload'] = json.loads(self.message['payload'])

    def __contains__(self, item: str) -> bool:
        return item in self.message

    def __getattr__(self, item: str) -> Any:
        if item in self.message:
            return self.message[item]

        raise AttributeError(f'There is no `{item}` in this '
                             f'{self.__class__.__name__}.')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(' \
               f'{pformat(self.message, sort_dicts=False)})'

    async def reply(self, **kwargs) -> int:
        """
        Send a reply for this message.

        :param kwargs: All the params of vk.messages.send method.
        :return: id of sent message (only for private messages).
        """

        return await self.vk.messages.send(peer_id=self.peer_id, **kwargs)

    async def chat_reply(self, **kwargs) -> int:
        """
        Send a reply for this message.

        :param kwargs: All the params of vk.messages.send method.
        :return: Conversation id of sent message.
        """

        res = await self.vk.messages.send(peer_ids=self.peer_id, **kwargs)
        return res[0]['conversation_message_id']


class MessageEvent:
    """Event received from user pressing callback button."""

    @property
    def is_private(self) -> bool:
        """Whether event was sent in private dialog."""

        return self.peer_id < 2e9

    def __init__(self, vk: "VK", message_event: dict[str, Any]):
        self.vk = vk
        self.message_event = message_event

    def __contains__(self, item: str) -> bool:
        return item in self.message_event

    def __getattr__(self, item: str) -> Any:
        if item in self.message_event:
            return self.message_event[item]

        raise AttributeError(f'There is no `{item}` in this '
                             f'{self.__class__.__name__}.')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(' \
               f'{pformat(self.message_event, sort_dicts=False)})'

    async def show_snackbar(self, text: str):
        """
        Show a snackbar with given text to the user.

        :param text: Text to show.
        :return: 'messages.sendMessageEventAnswer' response.
        """

        return await self.respond({'type': 'show_snackbar', 'text': text})

    async def open_link(self, link: str):
        """
        Open a link on the user's side.

        :param link: Link to open.
        :return: Same as vk.messages.sendMessageEventAnswer.
        """

        return await self.respond({'type': 'open_link', 'link': link})

    async def open_app(self, app_id: str, owner_id: Optional[int] = None,
                       hash_: Optional[str] = None):
        """
        Open VK Mini App.

        :param app_id: id of the app.
        :param owner_id: id of the community owning the app.
        :param hash_: Navigation hash for the app.
        :return: Same as vk.messages.sendMessageEventAnswer.
        """

        return await self.respond({
            'type': 'open_app', 'app_id': app_id,
            'owner_id': owner_id, 'hash': hash_
        })

    async def respond(self, event_data: dict[str, Any]):
        """
        Respond to event with given data.

        :param event_data: Data describing response.
        :return: Same as vk.messages.sendMessageEventAnswer.
        """

        return await self.vk.messages.sendMessageEventAnswer(
            event_id=self.event_id, user_id=self.user_id,
            peer_id=self.peer_id, event_data=self._dumps(event_data)
        )

    async def respond_from_payload(self):
        """
        Respond to the event with data from payload.

        :return: Same as vk.messages.sendMessageEventAnswer.
        """

        return await self.vk.messages.sendMessageEventAnswer(
            event_id=self.event_id, user_id=self.user_id,
            peer_id=self.peer_id, event_data=self._dumps(self.payload)
        )

    async def reply(self, **kwargs):
        """
        Send message in the chat in response to the event.

        :param kwargs: Params of vk.messages.send method.
        :return: id of sent message (only for private messages).
        """

        return await self.vk.messages.send(peer_id=self.peer_id, **kwargs)

    async def chat_reply(self, **kwargs) -> int:
        """
        Send message in the chat in response to the event.

        :param kwargs: All the params of vk.messages.send method.
        :return: Conversation id of sent message.
        """

        res = await self.vk.messages.send(peer_ids=self.peer_id, **kwargs)
        return res[0]['conversation_message_id']

    @staticmethod
    def _dumps(data: dict[str, Any]) -> str:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
