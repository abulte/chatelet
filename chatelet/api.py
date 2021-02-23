from urllib.parse import urlparse

from aiohttp import web, ClientSession, ClientTimeout
from aiohttp_apispec import (
    docs,
    request_schema,
    setup_aiohttp_apispec,
    validation_middleware,
)

from chatelet import config
from chatelet import schemas
from chatelet.db import Subscription
from chatelet.queue import queue, retry
from chatelet.log import log

api = web.Application()
routes = web.RouteTableDef()

if config.EAGER_QUEUES:
    import nest_asyncio
    nest_asyncio.apply()


@routes.view("/subscriptions/")
class SubscriptionsView(web.View):
    @docs(
        tags=["subscribe"],
        summary="List subscriptions",
        responses={
            200: {
                "schema": schemas.AddSubscriptionResponse(many=True),
                "description": "List of subscriptions",
            },
        },
    )
    async def get(self):
        subs = await Subscription.query.gino.all()
        return web.json_response([s.to_dict() for s in subs])

    @docs(
        tags=["subscribe"],
        summary="Add a subscription",
        responses={
            201: {
                "schema": schemas.AddSubscriptionResponse(),
                "description": "Subscription created",
            },
            200: {
                "schema": schemas.AddSubscriptionResponse(),
                "description": "Subscription already exists",
            },
            404: {"description": "Not found"},  # responses without schema
            422: {"description": "Validation error"},
        },
    )
    @request_schema(schemas.AddSubscription())
    async def post(self):
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
    # NB: using a new ClientSession for each dispatch is suboptimal
    # but how to reuse a session in worker threads?
    # TODO: apply event_filter
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
    @docs(
        tags=["publish"],
        summary="Publish an event",
        responses={
            201: {
                "description": "Publication created",
            },
            404: {"description": "Not found"},
            422: {"description": "Validation error"},
        },
    )
    @request_schema(schemas.AddPublication())
    async def post(self):
        data = await self.request.json()
        log.debug("Publishing: %s", data)
        subs = Subscription.query.where(Subscription.event == data["event"])
        for sub in await subs.gino.all():
            queue.enqueue(dispatch, sub, data, retry=retry)
        raise web.HTTPCreated()


api.add_routes(routes)
api.middlewares.append(validation_middleware)
setup_aiohttp_apispec(
    app=api,
    title="chatelet API",
    version="v1",
    url="/docs/swagger.json",
    swagger_path="/docs/",
)
