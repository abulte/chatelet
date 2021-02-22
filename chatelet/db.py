from gino.ext.aiohttp import Gino

db = Gino()


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer(), primary_key=True)
    event = db.Column(db.Unicode())
    event_filter = db.Column(db.Unicode())
    url = db.Column(db.Unicode())

    _idx1 = db.Index(
        "subscriptions_idx_url_event_event_filter",
        "event", "event_filter", "url",
        unique=True
    )
