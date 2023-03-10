"""Game accessor."""
__all__ = ['GameAccessor']

from contextlib import asynccontextmanager
from typing import Optional, Any, List, Tuple
import random

from sqlalchemy import select, Result, Select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..base import Accessor
from .models import Topic, Round, Player


# TODO move somewhere else
# http://gameshows.ru/wiki/Файл:ПЧ-барабан.png
wheel = [400, 650, 500, 750, 350, 1000, 700, 850, 600, 450, 800, 950] * 2


TurnResult = Tuple[bool, Round]


class GameAccessor(Accessor):
    """Game accessor. Handles game topic manipulations and game logic."""

    # Topics
    async def get_topic_by_id(self, id_) -> Optional[Topic]:
        """
        Get topic with specified id.

        :param id_: id of the topic.
        :return: Topic or None if it doesn't exist.
        """

        return await self._one_or_none(select(Topic).where(Topic.id == id_))

    async def list_topics(self) -> List[Topic]:
        """Get list of topics."""

        return await self._all(select(Topic))

    async def new_topic(self, word: str, description: str) -> Topic:
        """
        Create new topic.

        :param word: Word to guess.
        :param description: Description/hint for the word.
        :return: Created topic.
        """

        topic = Topic(word=word, description=description)

        async with self._session.begin() as session:
            session.add(topic)

        return topic

    async def update_topic(
            self, topic_id: int, word: str, description: str) -> Topic:
        """
        Update specified topic, replacing its word and description.

        :param topic_id: Topic to update.
        :param word: New word.
        :param description: New description.
        :return: Updated topic.
        """

        async with self._session.begin() as session:
            result = await session.execute(
                select(Topic).where(Topic.id == topic_id))
            topic = result.scalar_one()

            topic.word = word
            topic.description = description

        return topic

    async def delete_topic(self, topic_id: int):
        """
        Delete topic with specified id.

        :param topic_id: Topic to delete.
        """

        async with self._session.begin() as session:
            result = await session.execute(
                select(Topic).where(Topic.id == topic_id))
            topic = result.scalar_one()

            await session.delete(topic)

    async def random_topic(self) -> Topic:
        """
        Get random topic from all topics in the database.

        :return: Random topic.
        """

        return random.choice(await self._all(select(Topic)))

    # Rounds
    async def get_round_by_id(self, id_) -> Optional[Round]:
        """
        Get round with specified id.

        :param id_: id of the round.
        :return: Round or None if it doesn't exist.
        """

        return await self._one_or_none(select(Round).where(Round.id == id_))

    async def get_round_by_chat_id(self, chat_id) -> Optional[Round]:
        """
        Get round associated with specified chat id.

        :param chat_id: id of the chat where round takes place.
        :return: Round or None if it doesn't exist.
        """

        return await self._one_or_none(
            select(Round).where(Round.chat_id == chat_id)
            .order_by(Round.start_time.desc()).limit(1)
        )

    async def list_rounds(self, topic_id: int = None) -> List[Round]:
        """
        Get list of rounds. If topic_id is specified,
        only rounds with that topic are returned.

        :param topic_id: id of the topic, if any.
        :return: Found rounds.
        """

        statement: Select = select(Round)

        if topic_id is not None:
            statement = statement.where(Round.topic_id == topic_id)

        return await self._all(statement)

    # Players (do I even need these?)
    async def get_player_by_id(self, id_) -> Optional[Player]:
        """
        Get player record with specified id.

        :param id_: id of the player.
        :return: Player or None if it doesn't exist.
        """

        return await self._one_or_none(select(Player).where(Player.id == id_))

    async def list_players(self, round_id: int = None) -> List[Player]:
        """
        Get list of players. If round_id is specified,
        only players for that round are returned.

        :param round_id: id of the round, if any.
        :return: Found players.
        """

        statement = select(Player)

        if round_id is not None:
            statement = statement.where(Player.round_id == round_id)

        return await self._all(statement)

    # Game logic
    async def new_round(self, chat_id: int, topic_id: int) -> Round:
        """
        Create new round for a given chat with specified topic.

        :param chat_id: id of the chat to start round in.
        :param topic_id: id of the topic for the round.
        :return: Created round.
        """

        round_ = Round(chat_id=chat_id, topic_id=topic_id)

        async with self._session.begin() as session:
            session.add(round_)

        return round_

    async def join_round(self, round_id: int, user_id: int) -> TurnResult:
        """
        Add player to the round.

        :param round_id: Round to add player to.
        :param user_id: User to add to the round.
        :return: Whether round has enough players and the round itself.
        """

        async with self._round(round_id) as round_:
            return round_.add_player(user_id), round_

    async def spin_the_wheel(self, round_id: int) -> int:
        """
        Spin the wheel for given round.

        :param round_id: Round to spin the wheel for.
        :return: Score that was on the wheel.
        """

        score = random.choice(wheel)

        async with self._round(round_id) as round_:
            round_.set_score(score)

        return score

    async def say_letter(self, round_id: int, letter: str) -> TurnResult:
        """
        Make turn of saying one letter for given round.

        :param round_id: Round to make turn in.
        :param letter: Letter to say.
        :return: Whether the turn was successful and the round itself.
        """

        async with self._round(round_id) as round_:
            return round_.check_letter(letter), round_

    async def say_word(self, round_id: int, word: str) -> TurnResult:
        """
        Make turn of saying whole word for given round.

        :param round_id: Round to make turn in.
        :param word: Word to say.
        :return: Whether the turn was successful and the round itself.
        """

        async with self._round(round_id) as round_:
            return round_.check_word(word), round_

    # Utility methods
    @property
    def _session(self) -> async_sessionmaker:
        """For shorter context manager."""
        return self.app.database.session

    @asynccontextmanager
    async def _round(self, round_id: int) -> Round:
        """Context manager to have transaction and a round to work with."""

        async with self._session.begin() as session:
            result = await session.execute(
                select(Round).where(Round.id == round_id))
            yield result.unique().scalar_one()

    async def _one_or_none(self, statement: Select):
        """Helper method to get a single object or none."""

        async with self._session() as session:
            result: Result = await session.execute(statement)
            return result.unique().scalar_one_or_none()

    async def _all(self, statement: Select) -> List[Any]:
        """Helper method to get all objects returned."""

        async with self._session() as session:
            result: Result = await session.execute(statement)
            return result.unique().scalars().all()  # type: ignore
