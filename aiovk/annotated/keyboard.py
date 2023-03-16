"""Describes keyboard sent to user."""
__all__ = ['Keyboard', 'Color']

import json
from typing import Any


class Color:
    """Color of the button."""

    Primary = 'primary'
    Secondary = 'secondary'
    Positive = 'positive'
    Negative = 'negative'


class Keyboard:
    """Describes keyboard sent to user."""

    MAX_BUTTONS = 5
    MAX_LINES = 10
    MAX_LINES_INLINE = 6

    class Type:
        """Type of the button."""

        Text = 'text'
        Location = 'location'
        VKPay = 'vkpay'
        OpenApp = 'open_app'
        OpenLink = 'open_link'
        Callback = 'callback'

    def __init__(self, one_time: bool = False, inline: bool = False):
        self.one_time = one_time
        self.inline = inline

        self.buttons = [[]]

    @classmethod
    def empty(cls):
        """Returns empty keyboard (used to clear current keyboard)."""

        k = cls()
        k.buttons = []

        return k

    @property
    def _max_lines(self):
        return self.MAX_LINES_INLINE if self.inline else self.MAX_LINES

    def _add_button(self, button: dict[str, Any]):
        line = self.buttons[-1]
        if len(line) >= self.MAX_BUTTONS:
            raise ValueError(f'Too many buttons (max {self.MAX_BUTTONS})')

        line.append(button)

    @staticmethod
    def _dumps(data: Any) -> str:
        return json.dumps(
            data,
            ensure_ascii=False,
            separators=(',', ':'),  # Most compact json
            # default=... # conversion function for special classes ???
        )

    def to_dict(self) -> dict[str, Any]:
        """Returns keyboard as dict."""

        return {
            'inline': self.inline,
            'one_time': self.one_time,
            'buttons': self.buttons,
        }

    def to_json(self) -> str:
        """Returns keyboard as json string."""

        return self._dumps(self.to_dict())

    def new_line(self) -> "Keyboard":
        """Add new line to current keyboard.
        Can be chained with other methods."""

        if len(self.buttons) >= self._max_lines:
            raise ValueError(f'Too many lines (max {self._max_lines})')

        self.buttons.append([])
        return self

    def text_button(self, label: str, color: str = Color.Secondary,
                    payload: str | Any = None) -> "Keyboard":
        """
        Add text button to current row.
        Text button sends its label as text when pressed.

        Can be chained with other methods.

        :param label: Button text.
        :param color: Button color.
        :param payload: Will be sent as payload when button is clicked.
            Has to be a valid json string or JSON serializable.
        :return: This keyboard to chain methods.
        """

        if payload is not None and not isinstance(payload, str):
            payload = self._dumps(payload)

        self._add_button({
            'color': color,
            'action': {
                'type': self.Type.Text,
                'label': label,
                'payload': payload,
            },
        })

        return self

    def callback_button(self, label: str, color: str = Color.Secondary,
                        payload: str | Any = None) -> "Keyboard":
        """
        Add callback button to current row.
        Creates message_event when button is pressed. Does not send message.

        Can be chained with other methods.

        :param label: Button text.
        :param color: Button color.
        :param payload: Will be sent as payload when button is clicked.
            Has to be a valid json string or JSON serializable.
        :return: This keyboard to chain methods.
        """

        if payload is not None and not isinstance(payload, str):
            payload = self._dumps(payload)

        self._add_button({
            'color': color,
            'action': {
                'type': self.Type.Callback,
                'label': label,
                'payload': payload,
            },
        })

        return self

    def open_link_button(self, label: str, link: str,
                         payload: str | Any = None) -> "Keyboard":
        """
        Add open link button to current row.
        Opens link when button is pressed.

        Can be chained with other methods.

        :param label: Button text.
        :param link: Link to open.
        :param payload: Kept for backward compatibility.
        :return: This keyboard to chain methods.
        """

        if payload is not None and not isinstance(payload, str):
            payload = self._dumps(payload)

        self._add_button({
            'action': {
                'type': self.Type.OpenLink,
                'label': label,
                'link': link,
                'payload': payload,
            },
        })

        return self

    def location_button(self, payload: str | Any = None) -> "Keyboard":
        """
        Add location button to current row. Takes up whole row.
        Sends location to the dialog when button is pressed.

        Can be chained with other methods.

        :param payload: Kept for backward compatibility.
        :return: This keyboard to chain methods.
        """

        if len(self.buttons[-1]) != 0:
            raise ValueError('This type of button takes '
                             'the entire width of the line')

        if payload is not None and not isinstance(payload, str):
            payload = self._dumps(payload)

        self._add_button({
            'action': {
                'type': self.Type.Location,
                'payload': payload,
            },
        })

        return self

    def vkpay_button(self, hash_: str, payload: str | Any = None) -> "Keyboard":
        """
        Add vkpay button to current row. Takes up whole row.
        Opens payment window with payment specified by hash
        (see https://dev.vk.com/pay/getting-started).

        Can be chained with other methods.

        :param hash_: Payment parameters.
        :param payload: Kept for backward compatibility.
        :return: This keyboard to chain methods.
        """

        if len(self.buttons[-1]) != 0:
            raise ValueError('This type of button takes '
                             'the entire width of the line')

        if payload is not None and not isinstance(payload, str):
            payload = self._dumps(payload)

        self._add_button({
            'action': {
                'type': self.Type.VKPay,
                'hash': hash_,
                'payload': payload,
            },
        })

        return self

    def open_app_button(
            self, app_id: int, owner_id: int, label: str,
            hash_: str = None, payload: str | Any = None
    ) -> "Keyboard":
        """
        Add open app button to current row. Takes up whole row.
        Opens specified VK Mini App.

        Can be chained with other methods.

        :param app_id: id of the app to open.
        :param owner_id: id of the community owning the app.
        :param label: Name of the app, displayed on button.
        :param hash_: navigation hash for the app
            (will be sent after # in launch params).
        :param payload: Kept for backward compatibility.
        :return: This keyboard to chain methods.
        """

        if len(self.buttons[-1]) != 0:
            raise ValueError('This type of button takes '
                             'the entire width of the line')

        if payload is not None and not isinstance(payload, str):
            payload = self._dumps(payload)

        self._add_button({
            'action': {
                'type': self.Type.OpenApp,
                'app_id': app_id,
                'owner_id': owner_id,
                'label': label,
                'hash': hash_,
                'payload': payload,
            },
        })

        return self
