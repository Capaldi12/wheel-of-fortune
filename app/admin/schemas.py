"""Schemas for the admin module."""
__all__ = ['AdminSchema', 'AdminResponseSchema']

from marshmallow import Schema, fields

from ..schemas import OkResponseSchema


class AdminSchema(Schema):
    """Represents admin model."""

    id = fields.Int(dump_only=True, required=False)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class OneAdmin(Schema):
    """For requests/responses containing one admin."""

    admin = fields.Nested(AdminSchema)


class AdminResponseSchema(OkResponseSchema):
    """Response returning admin info."""

    data = fields.Nested(OneAdmin)
