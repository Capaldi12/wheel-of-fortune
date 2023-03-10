"""Views for the admin module."""
__all__ = ['routes']

from aiohttp.web import RouteTableDef, HTTPForbidden
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import new_session, get_session

from ..application import View
from ..middlewares import auth_required
from ..schemas import OkResponseSchema
from ..util import json_response

from .schemas import AdminSchema, AdminResponseSchema


# Routes for the module
routes = RouteTableDef()


@routes.view('/admin/login')
class AdminLoginView(View):
    """Authenticate as an admin."""

    @docs(summary='Admin login', tags=['admin'])
    @request_schema(AdminSchema)
    @response_schema(AdminResponseSchema)
    async def post(self):
        admin = await self.app.store.admins.get_by_email(self.data['email'])

        if admin is None or not admin.check_password(self.data['password']):
            raise HTTPForbidden(reason='Invalid email or password')

        user_session = await new_session(self.request)
        user_session['admin'] = AdminSchema().dump(admin)

        return json_response({'admin': AdminSchema().dump(admin)})


@routes.view('/admin/logout')
class AdminLogoutView(View):
    """Reset authentication."""

    @auth_required
    @docs(summary='Admin logout', tags=['admin'])
    @response_schema(OkResponseSchema)
    async def post(self):
        session = await get_session(self.request)
        session.invalidate()

        return json_response({})


@routes.view('/admin/current')
class AdminCurrentView(View):
    """Get the admin you are logged in as."""

    @auth_required
    @docs(summary='Current admin', tags=['admin'])
    @response_schema(AdminResponseSchema)
    async def get(self):
        return json_response({'admin': AdminSchema().dump(self.admin)})
