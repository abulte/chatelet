from urllib.parse import urlparse

import nest_asyncio

from aiohttp import web, ClientSession, ClientTimeout

from chatelet import config
from chatelet.db import Subscription
from chatelet.queue import queue, retry
from chatelet.log import log

api = web.Application()
routes = web.RouteTableDef()

if config.EAGER_QUEUES:
    nest_asyncio.apply()


@routes.view("/subscriptions/")
class SubscriptionsView(web.View):
    async def get(self):
        subs = await Subscription.query.gino.all()
        return web.json_response([s.to_dict() for s in subs])

    async def post(self):
        # TODO: validate request with marshmallow
        data = await self.request.json()

        sub = Subscription.query
        # TODO: handle a list of subscribable events
        sub = sub.where(Subscription.event == data["event"])
        sub = sub.where(Subscription.url == data["url"])
        sub = sub.where(Subscription.event_filter == data["event_filter"])
        sub = await sub.gino.first()
        if sub:
            return web.json_response(sub.to_dict(), status=200)

        parsed = urlparse(data["url"])
        if not any([parsed.netloc.endswith(d) for d in config.ALLOWED_DOMAINS]):
            raise web.HTTPForbidden()
        sub = await Subscription.create(**data)
        return web.json_response(sub.to_dict(), status=201)


async def dispatch(subscription, data):
    async with ClientSession(raise_for_status=True, timeout=ClientTimeout(total=15)) as client:
        log.debug("Dispatching to %s (%s)", subscription.url, subscription.id)
        await client.post(subscription.url, json={
            "ok": True,
            "event": subscription.event,
            "event_filter": subscription.event_filter,
            "subscription": subscription.id,
            "payload": data["payload"],
        })


@routes.view("/publications/")
class PublicationsView(web.View):
    async def post(self):
        data = await self.request.json()
        log.debug("Publishing: %s", data)
        subs = Subscription.query.where(Subscription.event == data["event"])
        # TODO: apply filter
        for sub in await subs.gino.all():
            queue.enqueue(dispatch, sub, data, retry=retry)
        raise web.HTTPCreated()


api.add_routes(routes)
