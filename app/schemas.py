"""Application schemas."""
__all__ = ['OkResponseSchema']

from marshmallow import Schema, fields


class OkResponseSchema(Schema):
    """Base success response."""

    status = fields.Str()
    data = fields.Dict()
