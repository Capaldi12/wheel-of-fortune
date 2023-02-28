from typing import Any, Optional

from .vk import VK

class ClientInfo:
    client_info: dict

    button_actions: list[str]
    keyboard: bool
    inline_keyboard: bool
    carousel: bool
    lang_id: int

    def __init__(self, client_info: Optional[dict[str, Any]] = ...) -> None: ...
    def __getattr__(self, item: str): ...
    def __contains__(self, item: str) -> bool: ...

class Message:
    vk: VK
    message: dict
    client_info: ClientInfo

    id: int
    date: int
    peer_id: int
    from_id: int
    text: str
    random_id: int
    out: bool
    conversation_message_id: int
    important: bool
    is_hidden: bool
    payload: Optional[str]
    attachments: list[dict[str, Any]]
    ref: Optional[str]
    ref_source: Optional[str]
    geo: Optional[dict[str, Any]]
    keyboard: Optional[dict[str, Any]]
    fwd_messages: list[dict[str, Any]]
    reply_message: Optional[dict[str, Any]]
    action: Optional[dict[str, Any]]
    admin_author_id: Optional[int]
    is_cropped: Optional[bool]
    members_count: Optional[int]
    update_time: Optional[int]
    was_listened: Optional[bool]
    pinned_at: Optional[int]
    message_tag: Optional[str]

    def __init__(self, vk: VK, message: dict[str, Any], client_info: Optional[dict[str, Any]] = ...) -> None: ...
    def __contains__(self, item: str) -> bool: ...
    def __getattr__(self, item: str) -> Any: ...
    async def reply(self, **kwargs): ...

class MessageEvent:
    vk: VK
    message_event: dict

    event_id: str
    user_id: int
    peer_id: int
    payload: dict[str, Any]

    def __init__(self, vk: VK, message_event: dict[str, Any]) -> None: ...
    def __contains__(self, item: str) -> bool: ...
    def __getattr__(self, item: str) -> Any: ...
    async def show_snackbar(self, text: str): ...
    async def open_link(self, link: str): ...
    async def open_app(self, app_id: str, owner_id: Optional[int] = ..., hash_: Optional[str] = ...): ...
    async def respond(self, event_data: dict[str, Any]): ...
    async def respond_from_payload(self): ...
    async def reply_with_message(self, **kwargs): ...
