from marshmallow import Schema, fields


class AddSubscription(Schema):
    url = fields.Url(required=True)
    event = fields.Str(required=True)
    event_filter = fields.Str(default=None)


class AddSubscriptionResponse(AddSubscription):
    id = fields.Int()
