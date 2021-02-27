from gino.ext.aiohttp import Gino

db = Gino()


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer(), primary_key=True)
    event = db.Column(db.Unicode())
    # this is actually a JSONPath (cf schemas) but stored as a string
    event_filter = db.Column(db.Unicode())
    url = db.Column(db.Unicode())
    active = db.Column(db.Boolean(), default=False)

    # FIXME: unique does not apply constraint
    _idx1 = db.Index(
        "subscriptions_idx_url_event_event_filter",
        "event", "event_filter", "url",
        unique=True
    )
