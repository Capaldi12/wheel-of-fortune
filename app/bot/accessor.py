"""Bot that handles the game."""
__all__ = ['BotAccessor']

import typing
from typing import Optional, Tuple, List
from traceback import print_exc

from aiovk.annotated import VK, Poller, \
    Message, MessageEvent, VKError, Keyboard, Color
from ..base import Accessor
from ..game.state import State

if typing.TYPE_CHECKING:
    from ..config import BotConfig
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

    async def startup(self, app: 'Application'):
        self.vk = VK(app.config.bot.token)
        self.poller = await self.vk.groups.getLongPollServer(
            group_id=app.config.bot.group_id)

        self.poller \
            .on('message_new', self.on_message_new) \
            .on('message_event', self.on_message_event) \
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

    @property
    def config(self) -> 'BotConfig':
        """Shortcut for self.app.config.bot"""

        return self.app.config.bot

    # Message handler and sub functions
    async def on_message_new(self, message: Message):
        """
        Handle new message.

        :param message: Message received.
        """

        # Just ignore messages without text and service messages
        if 'text' not in message or not message.text or 'action' in message:
            return

        # For error reporting
        self._current_peer = message.peer_id

        if message.is_private:
            await self.on_private_message(message)

        else:
            await self.on_chat_message(message)

        self._current_peer = None

    async def on_private_message(self, message: Message):
        """
        Handle private message.

        :param message: Message received.
        """

        # Button not supported
        if 'payload' in message and 'command' in message.payload:
            if message.payload['command'] == 'not_supported_button':
                return await message.reply(
                    message='Похоже, эта кнопка не работает на вашем клиенте. '
                            'Воспользуйтесь командой /check чтобы проверить '
                            'ваш клиент.'
                )

        elif message.text.lower() in {'/check', 'check'} or \
                ('payload' in message and
                 message.payload.get('action') == 'check'):

            return await self.check_client(message)

        elif message.text.lower() in {'/menu', 'menu'}:
            return await self.show_menu(message)

        elif message.text.lower() in {'/help', 'help'}:
            return await self.send_help(message)

        kb = Keyboard().open_app_button(
            self.config.app_id, -self.config.group_id, 'Пригласить в беседу')

        if self.config.chats:
            kb.new_line()
            for i, link in enumerate(self.config.chats):
                kb.open_link_button(f'Беседа {i + 1}', link)

        kb.new_line().text_button('Проверить клиент',
                                  payload={'action': 'check'})

        await message.reply(
            message='Добавьте меня в беседу чтобы сыграть в игру '
                    '(Не забудьте дать мне права администратора).\n'
                    'Или вы можете присоединиться к одной из готовых бесед.'
                    '\n\n(Если вы не видите клавиатуру, используйте /check '
                    'чтобы проверить возможности клиента, /menu для получения '
                    'меню в виде ссылок)',
            keyboard=kb
        )

    async def check_client(self, message: Message):
        """
        Check if user client is suitable for playing the game.

        :param message: Message from user.
        """

        text = 'Проверяю ваш клиент.\n\nНеобходимые функции:\n'

        basic_checks = {
            'Клавиатура': message.client_info.keyboard,
            'Клавиатура в сообщении': message.client_info.inline_keyboard,
            'Колбэк-кнопки': 'callback' in message.client_info.button_actions,
        }

        text += '\n'.join(
            [self._check(v, k) for k, v in basic_checks.items()]
        ) + '\n\nЖелательные функции:\n'

        extra_checks = {
            'Открытие приложений':
                'open_app' in message.client_info.button_actions,
            'Открытие ссылок':
                'open_link' in message.client_info.button_actions,
        }

        text += '\n'.join(
            [self._check(v, k) for k, v in extra_checks.items()]
        ) + '\n\n'

        if all(basic_checks.values()) and all(extra_checks.values()):
            text += 'Ваш клиент в полном порядке, проблем быть не должно.'
        elif all(basic_checks.values()):
            text += 'Игра будет работать, но будут проблемы с клавиатурой в ЛС.'
        else:
            text += (
                'Похоже, у вашего клиента не хватает возможностей. '
                'Попробуйте зайти в ВК из браузера или обновить приложение.'
            )

        await message.reply(message=text)

    async def show_menu(self, message: Message):
        """
        Show fallback text menu for when keyboard does not work.

        :param message: Message from user.
        """

        text = 'Меню (если не работает клавиатура):\n'

        text += f'@club{self.config.group_id}' \
                f'(Пригласить в беседу) (Нужно нажать "Добавить в чат")\n\n'

        text += 'Официальные беседы:\n'

        text += '\n'.join(link for link in self.config.chats)

        await message.reply(message=text, dont_parse_links=1)

    async def on_chat_message(self, message: Message):
        """
        Handle message from chat.

        :param message: Message received.
        """

        # TODO remove this after testing
        if self.debug and message.from_id == 155747201 \
                and 'ошибочк' in message.text.lower():
            raise Exception('Страшная-престрашная ошибка. Да-да!')

        if message.text.lower() in {'help', '/help'}:
            await self.send_help(message)
            return

        round_ = await self.game.get_round_by_chat_id(message.peer_id)

        # No active game
        if round_ is None or round_.current_state == State.finished:
            await self.new_round(message)

        elif message.text.lower() in {'stop', '/stop'}:
            await self.stop_round(message, round_)

        elif round_.current_state == State.starting:
            # TODO maybe should handle /leave here as well
            return  # Waiting for players to join and for game to start

        # After game started. To leve before use the button
        elif message.text.lower() in {'leave', '/leave'} \
                and message.from_id in round_.users:

            await self.leave_round(message, round_)

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
            # Should only happen when player is correct but stage is wheel
            await message.reply(message='А барабан крутить кто будет?')

    async def new_round(self, message: Message):
        """
        Create new round for chat form the message.

        :param message: Message received.
        """

        command, args = self._parse_command(message.text)

        if command == 'start':
            try:
                num = int(args[0]) if args else None
            except ValueError:
                await message.reply(
                    message='Количество участников должно быть цифрой!')
                return

            if num is not None:
                if num < 2:
                    await message.reply(
                        message='Ну нет, с таким количеством игроков '
                                'каши не сваришь. Нужно хотя бы 2'
                    )

                    return
                elif num > 10:  # TODO config ?
                    await message.reply(
                        message='Многовато будет игроков-то, не услежу за '
                                'всеми! Давайте-ка в пределах 10 человек.'
                    )
                    return

            topic = await self.game.random_topic()
            round_ = await self.game.new_round(message.peer_id, topic.id, num)

            cid = await message.chat_reply(
                message=self._make_join_message(round_),
                keyboard=self._keyboard_join(round_)
            )

            await self.vk.messages.pin(peer_id=message.peer_id,
                                       conversation_message_id=cid)

            await self.game.pin_message(round_.id, cid)

    async def stop_round(self, message: Message, round_: 'Round'):
        """
        Stop given round (and reply to the message).

        :param message: Message from chat with the round to stop.
        :param round_: Round to stop.
        """

        state = round_.current_state
        await self.game.end_round(round_.id)

        if round_.pinned_message is not None:
            await self.vk.messages.unpin(peer_id=round_.chat_id)

        if state == State.starting:
            await message.reply(
                message='Расходимся, кина не будет.'
            )
        else:
            await message.reply(
                message=f'А на этой ноте мы с вами прервёмся.'
                        f'\n\nОчки:\n{round_.final_scores()}'
            )

    async def leave_round(self, message: Message, round_: 'Round'):
        """
        Remove player from the round while the game is going.

        :param message: Message from player.
        :param round_: Round to remove player from.
        """

        mention = round_.get_player(message.from_id).mention()

        skip, round_ = await self.game.leave_round(round_.id, message.from_id)

        # One player left
        if len(round_.players) < 2:
            await self.game.end_round(round_.id)

            if round_.pinned_message is not None:
                await self.vk.messages.unpin(peer_id=round_.chat_id)

            await message.reply(
                message=f'Игрок {mention} покидает игру. В одного особо не '
                        f'поиграешь, да, {round_.current_player.mention()}?. '
                        f'Давайте закругляться тогда.'
                        f'\n\nОчки:\n{round_.final_scores()}'
            )

            return

        # Removed player was the one to make a turn
        if skip:
            await message.reply(
                message=f'Игрок {mention} покидает игру. '
                        f'Ваш ход, {round_.current_player.mention()}.',
                keyboard=self._keyboard_spin
            )
        else:
            await message.reply(
                message=f'Игрок {mention} покидает игру. Продолжаем.')

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

            # Update pinned message to reflect guessed state
            if success == 1:
                await self.vk.messages.edit(
                    peer_id=round_.chat_id,
                    conversation_message_id=round_.pinned_message,
                    message=self._make_topic_message(round_)
                )

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
                await self.vk.messages.unpin(peer_id=message.peer_id)

                await message.reply(
                    message=f'{round_.topic.word}! И у нас есть победитель!\n\n'
                            f'Победитель: {round_.winner.mention()}\n'
                            f'Очки:\n{round_.final_scores()}'
                )

        else:
            success, round_ = \
                await self.game.say_word(round_.id, text)

            if success:
                # Update pinned message with the full word
                await self.vk.messages.edit(
                    peer_id=message.peer_id,
                    conversation_message_id=round_.pinned_message,
                    message=self._make_topic_message(round_, True)
                )

                await self.vk.messages.unpin(peer_id=message.peer_id)

                await message.reply(
                    message=f'Правильно! {round_.topic.word}! '
                            f'И у нас есть победитель!\n\n'
                            f'Победитель: {round_.winner.mention()}\n'
                            f'Очки:\n{round_.final_scores()}'
                )

            else:
                await message.reply(
                    message=f'А вот и не угадали! Вращайте барабан, '
                            f'{round_.current_player.mention()}',
                    keyboard=self._keyboard_spin
                )

    @staticmethod
    async def send_help(message: Message):
        """
        Send help message.

        :param message: Message from user.
        """

        if message.is_private:
            await message.reply(
                message='Напишите мне любое сообщение, и я пришлю вам '
                        'клавиатуру. Или же вы можете использовать одну из '
                        'команд:\n/help - показать это сообщение.\n'
                        '/menu - показать меню в текстовой форме.\n'
                        '/check - проверить возможности вашего клиента.'
            )

        else:
            await message.reply(
                message='Команды:\n'
                        '/start [N] - Начать игру с N игроками '
                        '(3, если не указано).\n'
                        '/stop - Остановить игру.\n'
                        '/leave - Покинуть игру.\n'
                        '/help - Вы её сейчас читаете.\n\n'
                        'Если вы не видите кнопок "Присоединиться", '
                        '"Вращать барабан" и т.д. напишите мне в личные '
                        'сообщения, чтобы проверить возможности вашего клиента.'
            )

    # Event handler and sub functions
    async def on_message_event(self, event: MessageEvent):
        """
        Handle message event.

        :param event: Event to handle.
        """

        self._current_peer = event.peer_id

        if event.is_private:
            await self.on_private_event(event)

        else:
            await self.on_chat_event(event)

        self._current_peer = None

    async def on_private_event(self, event: MessageEvent):
        """
        Handle event in private messages.

        :param event: Event to handle.
        """

        if event.payload['action'] == 'counter':
            count = event.payload['count'] + 1

            await self.vk.messages.edit(
                peer_id=event.peer_id, message_id=event.payload['message_id'],
                message=event.payload['text'], keyboard=Keyboard(inline=True)
                .callback_button(str(count), payload={
                    'action': 'counter',
                    'count': count,
                    'message_id': event.payload['message_id'],
                    'text': event.payload['text'],
                })
            )

    async def on_chat_event(self, event: MessageEvent):
        """
        Handle event in chat.

        :param event: Event to handle.
        """

        round_ = await self.game.get_round_by_chat_id(event.peer_id)

        if round_ is None or round_.current_state == State.finished:
            await event.show_snackbar('А всё! А раньше надо было!')

        elif round_.current_state == State.starting:
            # TODO match case ?
            if event.payload['action'] == 'join':
                await self.handle_join(event, round_)

            elif event.payload['action'] == 'start':
                if event.user_id in round_.users:
                    if len(round_.players) == round_.player_count:
                        await self.start_round(event, round_)
                    else:
                        # This should not happen, but just in case
                        await event.show_snackbar('Погодите-ка')
                        await event.reply(
                            message='Так, а кто это убежал? '
                                    'Возвращайтесь, а то не начнём игру.'
                        )
                else:
                    await event.show_snackbar(
                        'А вы чего кнопку жмёте? Вы играете? '
                        'Нет. Ну так и нечего кнопку нажимать.'
                    )
            elif event.payload['action'] == 'leave':
                await self.handle_leave(event, round_)
            elif event.payload['action'] == 'too_many':
                await event.show_snackbar('Мест нету! Приходите завтра!')

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

    async def handle_join(self, event: MessageEvent, round_: 'Round'):
        """
        Handle join event.

        :param event: Received event.
        :param round_: Round to join.
        """

        if event.user_id not in round_.users or (
                # TODO remove this after testing
                self.debug and event.user_id == 155747201):

            # Who are you, friend?
            users = await self.vk.users.get(user_ids=event.user_id)
            name = users[0]['first_name']

            _, round_ = await self.game.join_round(
                round_.id, event.user_id, name)

            await event.show_snackbar('Вы присоединились к игре!')

            # Update pinned message
            await self.vk.messages.edit(
                peer_id=event.peer_id,
                conversation_message_id=round_.pinned_message,
                message=self._make_join_message(round_),
                keyboard=self._keyboard_join(round_)
            )

        else:
            await event.show_snackbar('А вы уже присоединились!')

    async def handle_leave(self, event: MessageEvent, round_: 'Round'):
        """
        Handle user leaving round before it has started.

        :param event: Received event.
        :param round_: Round to remove user from.
        """

        if event.user_id in round_.users:
            _, round_ = await self.game.leave_round(round_.id, event.user_id)

            await event.show_snackbar('Вы покинули игру!')

            # Update pinned message
            await self.vk.messages.edit(
                peer_id=event.peer_id,
                conversation_message_id=round_.pinned_message,
                message=self._make_join_message(round_),
                keyboard=self._keyboard_join(round_)
            )

        else:
            await event.show_snackbar('А вы и так не в игре!')

    async def handle_spin(self, event: MessageEvent, round_: 'Round'):
        """
        Handle spin the wheel event.

        :param event: Received event.
        :param round_: Round of the chat.
        """

        score = await self.game.spin_the_wheel(round_.id)
        await event.show_snackbar('Вжух!')
        await event.reply(
            message=f'{score} очков на барабане! '
                    f'Назовите букву или слово целиком'
        )

    async def start_round(self, event: MessageEvent, round_: 'Round'):
        """
        Actually start the round.

        :param event: Received event.
        :param round_: Round to start.
        """

        # Just clear keyboard
        await self.vk.messages.edit(
            peer_id=event.peer_id,
            conversation_message_id=round_.pinned_message,
            message=self._make_join_message(round_),
            keyboard=Keyboard.empty()
        )

        round_ = await self.game.start_round(round_.id)

        await event.show_snackbar('Начинаем игру!')
        await event.reply(message='А мы начинаем игру. Ваше слово:')

        # Topic message, which will be edited on every new letter
        cid = await event.chat_reply(message=self._make_topic_message(round_))
        await self.vk.messages.pin(peer_id=event.peer_id,
                                   conversation_message_id=cid)
        await self.game.pin_message(round_.id, cid)

        # Invite to first turn
        await event.reply(
            message=f'Первый ход за вами, {round_.current_player.mention()}. '
                    f'Вращайте барабан.',
            keyboard=self._keyboard_spin
        )

    # ---
    async def on_error(self, e: Exception):
        """
        Handle error, that happened during message handling.

        :param e: Error to handle.
        :return: Whether the error was handled.
        """

        print('Error in BotAccessor:')
        print_exc()

        if self.debug and self._current_peer is not None:
            try:
                await self.vk.messages.send(
                    peer_id=self._current_peer,
                    message=f'Вот те незадача! Ошибочка вышла:'
                            f'\n\n{e.__class__.__name__}: {e}'
                )
            except VKError:
                print_exc()

            self._current_peer = None

        return True

    # Helpers
    @staticmethod
    def _parse_command(text: str) -> Tuple[str, List[str]]:
        command, *arguments = text.split()

        return command.replace('/', '').lower(), arguments

    @staticmethod
    def _make_join_message(round_: 'Round') -> str:
        # TODO separate class for this stuff
        msg = f'Объявляется набор игроков!\n\n' \
              f'Участники ({len(round_.players)}/{round_.player_count})'

        if len(round_.players) > 0:
            msg += ':\n' + '\n'.join(p.mention() for p in round_.players)

        return msg

    @staticmethod
    def _make_topic_message(round_: 'Round', full_word: bool = False) -> str:
        word = ' '.join(round_.topic.word.upper()) \
            if full_word else round_.display_word

        # This dash is here to separate word from description
        # in pinned message form which lacks line breaks
        return f'{word}\n\n— {round_.topic.description}'

    @staticmethod
    def _keyboard_join(round_: 'Round') -> Keyboard:
        at_least_one = len(round_.players) > 0
        has_enough = len(round_.players) == round_.player_count

        k = Keyboard(inline=True).callback_button(
            'Присоединиться',
            Color.Positive if not has_enough else Color.Secondary,
            {'action': 'join'} if not has_enough else {'action': 'too_many'}
        ).callback_button(
            'Покинуть игру',
            Color.Negative if at_least_one else Color.Secondary,
            {'action': 'leave'}
        )

        if has_enough:
            k.new_line().callback_button(
                'Начать игру', Color.Positive, {'action': 'start'}
            )

        return k

    @staticmethod
    def _check(check: bool, text: str) -> str:
        return {True: '✔️', False: '❌️'}.get(check) + ' ' + text
