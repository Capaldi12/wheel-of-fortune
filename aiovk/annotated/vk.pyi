"""Annotated version of VK API wrapper."""
from ..base import VK as BaseVK, \
    MethodGroup as MethodGroup, Method as Method, VKError as VKError
from .poller import Poller
from .keyboard import Keyboard
from typing import Any

Attachments = str

class VK(BaseVK):
    """Annotated version of VK API wrapper."""
    groups: Groups
    messages: Messages

    def __aenter__(self) -> VK: ...

    async def before_request(self, method: str, params: dict[str, Any]) -> None: ...
    async def _process_before_rule(self, match: str, params: dict[str, Any]) -> dict[str, Any]: ...
    async def after_request(self, method: str, data: dict[str, Any]) -> Any: ...

class Groups(MethodGroup):
    async def getLongPollServer(self, *, group_id: int | str) -> Poller:
        """
        Returns poller for long polling server.

        :param group_id: id of group.
        :return: Object of poller.
        """

class Messages(MethodGroup):
    async def send(
        self, *, user_id: int = ..., random_id: int = ..., peer_id: int = ...,
        peer_ids: int | str = ..., domain: str =..., chat_id: int = ..., user_ids: str =...,
        message: str = ..., guid: int = ..., lat: str = ..., long: str = ...,
        attachment: Attachments = ..., reply_to: int = ..., forward_messages: str = ...,
        forward: str = ..., sticker_id: int =..., group_id: int =...,
        keyboard: Keyboard = ..., template: str = ..., payload: str = ...,
        content_source: str = ..., dont_parse_links: bool =...,
        disable_mentions: bool =..., intent: str = ..., subscribe_id: int = ...
    ) -> int | list[dict[str, Any]]:
        """
        Sends message. See https://dev.vk.com/method/messages.send for reference.

        Example:

            vk.messages.send(peer_id=123456789, message='Hello!', random_id=123)

        At least one of `user_id`, `user_ids`, `peer_id`, `peer_ids`, `domain`, `chat_id` is required.

        :param user_id: User to send message to.
        :param random_id: Unique id to prevent repeated message receiving. Attached to app id and sender id.
        :param peer_id: Destination id. `id` for user, `2000000000 + id` for chat, `-id` for group.
        :param peer_ids: Destination ids for multiple destinations.
        :param domain: Short user address (e.g. `illarionov`).
        :param chat_id: id of the chat to send message to.
        :param user_ids: User ids for multiple users.
        :param message: Text of the message. Required if `attachment` is not specified.
        :param guid: Global unique id to prevent repeated message sending.
        :param lat: Geographical latitude.
        :param long: Geographical longitude.
        :param attachment: Media attachment for message. Required if `message` is not specified.
        :param reply_to: id of the message to reply to.
        :param forward_messages: ids of the message to forward.
        :param forward: Messages to forward.
        :param sticker_id: id of the sticker to send.
        :param group_id: id of the group (if message is sent from community).
        :param keyboard: Keyboard for message.
        :param template: Template of the message (see https://dev.vk.com/api/bots/development/messages#Шаблоны%20сообщений).
        :param payload: Message payload.
        :param content_source: Source for message content (see https://dev.vk.com/api/bots/development/messages#Сообщения%20с%20пользовательским%20контентом).
        :param dont_parse_links: Don't create snippet with url in message.
        :param disable_mentions: Don't notify mentioned in the message.
        :param intent: String describing intent.
        :param subscribe_id: Reserved for future use when working with intents.
        :return: id of sent message or, if `peer_ids` was used, array of objects, describing sent messages.
        """

    async def edit(
            self, *, peer_id: int = ..., message_id: int =...,
            conversation_message_id: int = ..., message: str = ...,
            keep_forward_messages: int = ..., keep_snippets: int =...,
            dont_parse_links: int =..., disable_mentions: int =...,
            group_id: int =..., lat: float = ..., long: float =...,
            attachment: Attachments = ..., keyboard: Keyboard =...,
            template: str =...,
    ) -> int:
        """
        Edit the message. See https://dev.vk.com/method/messages.edit for reference.

        :param peer_id: id of the dialog.
        :param message_id: id of the message.
        :param conversation_message_id: conversation id of the message.
        :param message: New text of the message.
        :param keep_forward_messages: 1 to keep forwarded messages.
        :param keep_snippets: 1 to keep snippets.
        :param dont_parse_links: 1 to not parse links.
        :param disable_mentions: 1 to disable mentions.
        :param group_id: id of the group (for community messages with user access key).
        :param lat: Geographical latitude.
        :param long: Geographical longitude.
        :param attachment: Media attachment for message.
        :param keyboard: Keyboard object.
        :param template: Template of the message.
        :return: 1.
        """
    async def sendMessageEventAnswer(self, *, event_id: str, user_id: int,
                                     peer_id: int, event_data: str) -> int:
        """
        Send response to message event (sent when callback button is pressed).

        :param event_id: id of the event.
        :param user_id: id of the user triggering the event.
        :param peer_id: id of the dialog of the event.
        :param event_data: Action to perform (see https://dev.vk.com/api/bots/development/keyboard#Callback-кнопки).
        :return: Number 1, for some reason?
        """

    async def pin(self, *, peer_id, message_id: int = ...,
                  conversation_message_id: int = ...) -> dict[str, Any]:
        """
        Pin message with given message_id or conversation_message_id.

        :param peer_id: id of the dialog.
        :param message_id: Message id (only for private messages).
        :param conversation_message_id: id of the message in the conversation.
        :return: Object of pinned message.
        """

    async def unpin(self, *, peer_id, group_id: int =...) -> int:
        """
        Unpin message in given chat.

        :param peer_id: id of the dialog.
        :param group_id: Group id (for community messages with user access key).
        :return: 1.
        """
