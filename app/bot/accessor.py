"""Bot that handles the game."""
__all__ = ['BotAccessor']

import typing
from typing import Optional
from traceback import print_exc

from aiovk.annotated import VK, Poller, \
    Message, MessageEvent, VKError, Keyboard, Color
from ..base import Accessor
from ..game.state import State

if typing.TYPE_CHECKING:
    from ..application import Application
    from ..game import GameAccessor
    from ..game.models import Round


class BotAccessor(Accessor):
    """Bot that handles the game."""

    vk: VK
    poller: Poller

    # For debug purposes
    _current_peer: Optional[int]

    # Keyboards
    _keyboard_spin = Keyboard(inline=True) \
        .callback_button('Вращать барабан', Color.Primary, {'action': 'spin'})

    _keyboard_join = Keyboard(inline=True) \
        .callback_button('Присоединиться', Color.Positive, {'action': 'join'})

    async def startup(self, app: 'Application'):
        self.vk = VK(app.config.bot.token)
        self.poller = await self.vk.groups.getLongPollServer(
            group_id=app.config.bot.group_id)

        self.poller \
            .on('message_new', self.on_message_new) \
            .on('message_event', self.on_message_event) \
            .ignore('message_reply') \
            .ignore('message_typing_state') \
            .on_error(self.on_error)

        await self.poller.start_polling()

    async def cleanup(self, app: 'Application'):
        await self.poller.stop_polling()
        await self.vk.dispose()

    @property
    def game(self) -> 'GameAccessor':
        """Shortcut for self.app.store.game"""

        return self.app.store.game

    @property
    def debug(self) -> bool:
        """Shortcut for self.app.config.bot.debug"""

        return self.app.config.bot.debug

    # Message handler and sub functions
    async def on_message_new(self, message: Message):
        """
        Handle new message.

        :param message: Message received.
        """

        if 'text' not in message or 'action' in message:
            return

        # For error reporting
        self._current_peer = message.peer_id

        if message.peer_id > 2e9:
            await self.on_chat_message(message)

        else:
            await self.on_private_message(message)

        self._current_peer = None

    async def on_private_message(self, message: Message):
        """
        Handle private message.

        :param message: Message received.
        """

        await message.reply(
            message='Добавь меня в беседу чтобы сыграть в игру.'
        )

    async def on_chat_message(self, message: Message):
        """
        Handle message from chat.

        :param message: Message received.
        """

        round_ = await self.game.get_round_by_chat_id(message.peer_id)

        # No active game
        if round_ is None or round_.current_state == State.finished:
            await self.start_round(message)

        elif message.text.lower() in {'stop', '/stop'}:
            await self.stop_round(message, round_)

        elif round_.current_state == State.starting:
            pass  # Just ignore, we wait for players to join (using button)

        elif round_.current_player.user_id != message.from_id:
            if message.from_id in round_.users:
                await message.reply(
                    message='Дождитесь своего хода, пожалуйста.')
            else:
                await message.reply(
                    message='Никакой помощи из зала!')

        elif round_.current_state == State.player_turn:
            await self.player_turn(message, round_)
        else:
            await message.reply(message='А барабан крутить кто будет?')

    async def start_round(self, message: Message):
        """
        Start new round for chat form the message.

        :param message: Message received.
        """

        if message.text.lower() in {'start', '/start'}:
            topic = await self.game.random_topic()
            await self.game.new_round(message.peer_id, topic.id)

            await message.reply(
                message='А кто играть будет?',
                keyboard=self._keyboard_join
            )

    async def stop_round(self, message: Message, round_: 'Round'):
        """
        Stop given round (and reply to the message).

        :param message: Message from chat with the round to stop.
        :param round_: Round to stop.
        """

        state = round_.current_state
        await self.game.end_round(round_.id)

        if state == State.starting:
            await message.reply(
                message='Расходимся, кина не будет.'
            )
        else:
            await message.reply(
                message=f'А на этой ноте мы с вами прервёмся.'
                        f'\n\nОчки:\n{round_.final_scores()}'
            )

    async def player_turn(self, message: Message, round_: 'Round'):
        """
        Perform player turn.

        :param message: Message from player.
        :param round_: Current round.
        """

        text = message.text.lower()

        if len(text) == 1:
            success, round_ = \
                await self.game.say_letter(round_.id, text)

            if success == -1:
                await message.reply(
                    message=f'Нет такой буквы! Вращайте барабан, '
                            f'{round_.current_player.mention()}',
                    keyboard=self._keyboard_spin
                )
            elif success == 0:
                await message.reply(
                    message=f'Уже была такая буква! Вращайте барабан, '
                            f'{round_.current_player.mention()}',
                    keyboard=self._keyboard_spin
                )

            elif round_.current_state != State.finished:
                await message.reply(
                    message=f'Откройте букву {text.upper()}!\n\n'
                            f'{round_.display_word}\n\nВращайте барабан.',
                    keyboard=self._keyboard_spin
                )

            else:
                await message.reply(
                    message=f'{round_.topic.word}! И у нас есть победитель!'
                            f'\n\nОчки:\n{round_.final_scores()}'
                )

        else:
            success, round_ = \
                await self.game.say_word(round_.id, text)

            if success:
                await message.reply(
                    message=f'Правильно! {round_.topic.word}! '
                            f'И у нас есть победитель!'
                            f'\n\nОчки:\n{round_.final_scores()}'
                )

            else:
                await message.reply(
                    message=f'А вот и не угадали! Вращайте барабан, '
                            f'{round_.current_player.mention()}',
                    keyboard=self._keyboard_spin
                )

    # Event handler and sub functions
    async def on_message_event(self, event: MessageEvent):
        """
        Handle message event.

        :param event: Event to handle.
        """

        self._current_peer = event.peer_id

        round_ = await self.game.get_round_by_chat_id(event.peer_id)

        if round_ is None or round_.current_state == State.finished:
            await event.show_snackbar('А всё! А раньше надо было!')

        elif round_.current_state == State.starting and \
                event.payload['action'] == 'join':

            await self.handle_join(event, round_)

        elif round_.current_player.user_id != event.user_id:
            if event.payload['action'] == 'spin':
                await event.show_snackbar('Да не вы!')
            else:
                await event.show_snackbar('Набор завершён, приходите завтра')

        elif round_.current_state == State.wheel and \
                event.payload['action'] == 'spin':

            await self.handle_spin(event, round_)

        else:
            await event.show_snackbar('Что-то не то вы делаете, друг мой!')

        self._current_peer = None

    async def handle_join(self, event: MessageEvent, round_: 'Round'):
        """
        Handle join event.

        :param event: Received event.
        :param round_: Round to join.
        """

        can_start = False

        if event.user_id not in round_.users:

            users = await self.vk.users.get(user_ids=event.user_id)
            name = users[0]['first_name']

            can_start, round_ = await self.game.join_round(
                round_.id, event.user_id, name)

            await event.show_snackbar('Вы присоединились к игре!')

        else:
            await event.show_snackbar('А вы уже присоединились!')

        if can_start:
            await event.reply_with_message(
                message=f'А мы начинаем игру. Ваше слово:\n\n'
                f'{round_.display_word}\n\n{round_.topic.description}\n\n'
                f'Первый ход за вами, {round_.current_player.mention()}. '
                f'Вращайте барабан.',
                keyboard=self._keyboard_spin
            )

    async def handle_spin(self, event: MessageEvent, round_: 'Round'):
        """
        Handle spin the wheel event.

        :param event: Received event.
        :param round_: Round of the chat.
        """

        score = await self.game.spin_the_wheel(round_.id)
        await event.show_snackbar('Вжух!')
        await event.reply_with_message(
            message=f'{score} очков на барабане! Назовите букву'
        )

    # ---
    async def on_error(self, e: Exception):
        """
        Handle error, that happened during message handling.

        :param e: Error to handle.
        :return: Whether the error was handled.
        """

        print_exc()

        if self.debug and self._current_peer is not None:
            try:
                await self.vk.messages.send(
                    peer_id=self._current_peer,
                    message=f'Ошибочка вышла:\n\n{e.__class__.__name__}: {e}'
                )
            except VKError:
                print_exc()

            self._current_peer = None

        return True
