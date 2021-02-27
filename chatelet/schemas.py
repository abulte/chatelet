from jsonpath2.path import Path as JSONPath
from marshmallow import Schema, fields, ValidationError


class JSONPathField(fields.Str):
    """A JSONPath expression field"""

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return
        try:
            JSONPath.parse_str(value)
            return value
        except ValueError as error:
            raise ValidationError("Not a valid JSONPath.") from error


class AddSubscription(Schema):
    url = fields.Url(required=True)
    event = fields.Str(required=True)
    event_filter = JSONPathField(default=None)


class AddSubscriptionResponse(AddSubscription):
    id = fields.Int()
    active = fields.Boolean()


class AddPublication(Schema):
    event = fields.Str(required=True)
    payload = fields.Dict(required=True)


class DispatchEvent(Schema):
    """This a dummy schema to document the dispatch payload"""
    ok = fields.Bool()
    subscription = fields.Int()
    event = fields.Str(required=True)
    payload = fields.Dict()


class HookSecretSchema(Schema):
    class Meta:
        fields = ("x-hook-secret", )
