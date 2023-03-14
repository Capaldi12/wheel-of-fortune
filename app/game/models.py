"""Models for the game."""
__all__ = ['Topic', 'Round', 'Player']

import re
from typing import List, Optional
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .state import State


# TODO make into field of the Round class (required on creation)
N_PLAYERS = 3


class Topic(Base):
    """Topic of the round. Represents word to guess."""

    __tablename__ = 'topic'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    word: Mapped[str]
    description: Mapped[str]

    rounds: Mapped[List['Round']] = relationship(
        back_populates='topic', init=False)

    def __contains__(self, letter: str) -> bool:
        return letter.lower() in self.word.lower()

    def mask(self, letters: str) -> str:
        """Return the word with letters not in `letters` masked."""

        letters = letters.lower()

        return ''.join(letter if letter.lower() in letters else '_'
                       for letter in self.word)


class Round(Base):
    """Single round of the game."""

    __tablename__ = 'round'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    chat_id: Mapped[int]

    topic_id: Mapped[int] = mapped_column(ForeignKey('topic.id'), default=None)
    topic: Mapped['Topic'] = relationship(
        back_populates='rounds', default=None, lazy='joined')

    guessed_letters: Mapped[str] = mapped_column(default='')
    current_state: Mapped[int] = mapped_column(default=State.starting)
    current_player_order: Mapped[int] = mapped_column(default=0)
    score_up_next: Mapped[int] = mapped_column(default=0)

    start_time: Mapped[datetime] = mapped_column(default_factory=datetime.now)
    last_turn: Mapped[datetime] = mapped_column(default_factory=datetime.now)

    winner_id: Mapped[int] = mapped_column(default=-1)

    players: Mapped[List['Player']] = relationship(
        back_populates='round', init=False,
        cascade='all, delete-orphan', lazy='joined'
    )

    def mask(self) -> str:
        """Return masked word using guessed letters."""

        return self.topic.mask(self.guessed_letters)

    @property
    def display_word(self) -> str:
        word = self.mask().replace('_', '▯').upper()
        # Space between letters, but not between ▯ (they bring their own)
        return re.sub(r"(?<!^)(\B)(?!$|▯)", " ", word)

    @property
    def current_player(self) -> 'Player':
        """Return current player."""

        return next(p for p in self.players
                    if p.order == self.current_player_order)

    @property
    def users(self) -> List[int]:
        return [p.user_id for p in self.players]

    def final_scores(self) -> str:
        return '\n'.join(
            f'{p.mention()} - {p.score}'
            for p in sorted(self.players, key=lambda p: p.score, reverse=True)
        )

    def next_player(self):
        """Set next player"""

        self.current_player_order = (self.current_player_order + 1) % N_PLAYERS
        self.current_state = State.wheel

    def check_letter(self, letter: str) -> int:
        """Make turn with a letter."""

        letter = letter.lower()

        # Already guessed
        if letter in self.guessed_letters:
            self.next_player()
            return 0  # TODO fix magic number

        # No such letter
        if letter not in self.topic:
            self.guessed_letters += letter
            self.next_player()
            return -1

        # Guessed correctly
        self.guessed_letters += letter
        self.current_state = State.wheel
        self.current_player.score += \
            self.score_up_next * self.topic.word.lower().count(letter)

        # Win condition
        if '_' not in self.mask():
            self.current_state = State.finished
            self.winner_id = self.current_player.user_id

        return 1

    def check_word(self, word) -> bool:
        """Make turn with a word."""

        if word.lower() == self.topic.word.lower():
            self.current_state = State.finished
            self.current_player.score += \
                self.score_up_next * self.mask().count('_')
            self.winner_id = self.current_player.user_id

            return True

        self.next_player()
        return False

    def set_score(self, score: int):
        """Set result of the wheel spin."""

        self.score_up_next = score  # type: ignore
        self.current_state = State.player_turn

    def add_player(self, user_id: int, name: str) -> bool:
        """Add a player to the round."""

        self.players.append(
            Player(user_id=user_id, name=name, order=len(self.players)))

        if len(self.players) == N_PLAYERS:
            self.current_state = State.wheel
            return True

        return False

    def end_round(self):
        """End the round prematurely."""

        self.current_state = State.finished


class Player(Base):
    """Player record for the round."""

    __tablename__ = 'player'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    user_id: Mapped[int]
    name: Mapped[Optional[str]] = mapped_column(default=None)

    round_id: Mapped[int] = mapped_column(ForeignKey('round.id'), default=None)
    round: Mapped['Round'] = relationship(
        back_populates='players', default=None, lazy='joined')

    order: Mapped[int] = mapped_column(default=0)
    score: Mapped[int] = mapped_column(default=0)

    def mention(self):
        return f'[id{self.user_id}|{self.name if self.name else "Игрок"}]'
