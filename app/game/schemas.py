"""Schemas for the game."""
__all__ = [
    'TopicSchema', 'PlayersSchema', 'RoundSchema',
    'OneTopic', 'TopicList', 'OneRound', 'RoundList',
    'TopicResponseSchema', 'TopicListResponseSchema',
    'RoundResponseSchema', 'RoundListResponseSchema',
    'RoundId'
]

from marshmallow import Schema, fields, post_dump

from ..schemas import OkResponseSchema
from .state import State


# Model schemas
class TopicSchema(Schema):
    """A topic."""

    id = fields.Integer(dump_only=True)
    word = fields.String(required=True)
    description = fields.String(required=True)


# These two schemas are only used to dump and don't need to load data
class PlayersSchema(Schema):
    """Player of the round."""

    user_id = fields.Integer()
    order = fields.Integer()
    score = fields.Integer()


class RoundSchema(Schema):
    """A round."""

    id = fields.Integer()
    chat_id = fields.Integer()
    topic = fields.Nested(TopicSchema)
    guessed_letters = fields.String()
    current_state = fields.Integer()
    current_player_order = fields.Integer()
    score_up_next = fields.Integer()
    start_time = fields.DateTime()
    last_turn = fields.DateTime()
    winner_id = fields.Integer()
    players = fields.List(fields.Nested(PlayersSchema))

    @post_dump
    def string_state(self, data, **kwargs):
        data['current_state'] = State.names[data['current_state']]
        return data


# Auxiliary schemas
class OneTopic(Schema):
    """When one topic is requested."""

    topic = fields.Nested(TopicSchema)


class TopicList(Schema):
    """List of topics."""

    topics = fields.List(fields.Nested(TopicSchema))


class OneRound(Schema):
    """When one round is requested."""

    round = fields.Nested(RoundSchema)


class RoundList(Schema):
    """List of rounds."""
    rounds = fields.List(fields.Nested(RoundSchema))


# Response schemas
class TopicResponseSchema(OkResponseSchema):
    """Response with a topic."""

    data = fields.Nested(OneTopic)


class TopicListResponseSchema(OkResponseSchema):
    """Response with a list of topics."""

    data = fields.Nested(TopicList)


class RoundResponseSchema(OkResponseSchema):
    """Response with a round."""

    data = fields.Nested(OneRound)


class RoundListResponseSchema(OkResponseSchema):
    """Response with a list of rounds."""

    data = fields.Nested(RoundList)


# Query schemas
class RoundId(Schema):
    """Querystring with round id."""

    round_id = fields.Integer(required=False)
