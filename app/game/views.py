"""Views for game module."""

from aiohttp.web import RouteTableDef, HTTPNotFound, HTTPConflict
from aiohttp_apispec import docs, response_schema, request_schema, \
    querystring_schema
from sqlalchemy.exc import NoResultFound, IntegrityError

from .schemas import *
from ..application import View
from ..middlewares import auth_required
from ..schemas import OkResponseSchema
from ..util import json_response

routes = RouteTableDef()


@routes.view('/game/topic')
class TopicListView(View):
    """Creating a topic and viewing topics."""

    @docs(summary='Get a list of topics', tags=['game/topic'])
    @response_schema(TopicListResponseSchema)
    @auth_required
    async def get(self):
        """Get a list of topics."""

        topics = await self.app.store.game.list_topics()

        return json_response(TopicList().dump({'topics': topics}))

    @docs(summary='Create a new topic', tags=['game/topic'])
    @request_schema(TopicSchema)
    @response_schema(TopicResponseSchema)
    @auth_required
    async def post(self):
        """Create a new topic."""

        topic = await self.app.store.game.new_topic(
            self.data['word'], self.data['description'])

        return json_response(OneTopic().dump({'topic': topic}))


@routes.view('/game/topic/{topic_id}')
class TopicView(View):
    """Working with single topic."""

    @property
    def topic_id(self):
        """Topic id from request."""

        return int(self.request.match_info['topic_id'])

    @docs(summary='Get topic with given id', tags=['game/topic'])
    @response_schema(TopicResponseSchema)
    @auth_required
    async def get(self):
        """Get topic with given id."""

        topic = await self.app.store.game.get_topic_by_id(self.topic_id)

        if topic is None:
            raise HTTPNotFound(reason='No topic with given id')

        return json_response(OneTopic().dump({'topic': topic}))

    @docs(summary='Update topic with given id', tags=['game/topic'])
    @request_schema(TopicSchema)
    @response_schema(TopicResponseSchema)
    @auth_required
    async def put(self):
        """Update topic with given id."""

        try:
            topic = await self.app.store.game.update_topic(
                self.topic_id, self.data['word'], self.data['description'])

        except NoResultFound:
            raise HTTPNotFound(reason='No topic with given id') from None

        return json_response(OneTopic().dump({'topic': topic}))

    @docs(summary='Delete topic with given id', tags=['game/topic'])
    @response_schema(OkResponseSchema)
    @auth_required
    async def delete(self):
        """Delete topic with given id."""

        try:
            await self.app.store.game.delete_topic(self.topic_id)

        except NoResultFound:
            raise HTTPNotFound(reason='No topic with given id') from None

        except IntegrityError:
            raise HTTPConflict(
                reason='There are rounds using this topic') from None

        return json_response({})


@routes.view('/game/round')
class RoundListView(View):
    """Get a list of rounds."""

    @docs(summary='Get a list of rounds', tags=['game/round'])
    @querystring_schema(RoundId)
    @response_schema(RoundListResponseSchema)
    @auth_required
    async def get(self):
        """Get a list of rounds."""

        rounds = await self.app.store.game.list_rounds(
            self.data.get('round_id'))

        return json_response(RoundList().dump({'rounds': rounds}))


@routes.view('/game/round/{round_id}')
class RoundView(View):
    """Working with single round."""

    @docs(summary='Get round with given id', tags=['game/round'])
    @response_schema(RoundResponseSchema)
    @auth_required
    async def get(self):
        """Get round with given id."""

        round_id = int(self.request.match_info['round_id'])

        round_ = await self.app.store.game.get_round_by_id(round_id)

        if round_ is None:
            raise HTTPNotFound(reason='No round with given id')

        return json_response(OneRound().dump({'round': round_}))
