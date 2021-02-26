from marshmallow import Schema, fields


class AddSubscription(Schema):
    url = fields.Url(required=True)
    event = fields.Str(required=True)
    # TODO: move to json (for types)
    event_filter = fields.Str(default=None)


class AddSubscriptionResponse(AddSubscription):
    id = fields.Int()


class AddPublication(Schema):
    event = fields.Str(required=True)
    payload = fields.Dict(required=True)


class DispatchEvent(Schema):
    """This a dummy schema to document the dispatch payload"""
    ok = fields.Bool()
    subscription = fields.Int()
    event = fields.Str(required=True)
    payload = fields.Dict()
