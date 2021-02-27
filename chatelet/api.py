from uuid import uuid4
from urllib.parse import urlparse

from aiohttp import web, ClientSession, ClientTimeout
from aiohttp_apispec import (
    docs,
    request_schema,
    setup_aiohttp_apispec,
    validation_middleware,
    headers_schema,
)
from jsonpath2.path import Path

from chatelet import config
from chatelet import schemas
from chatelet.db import Subscription
from chatelet.queue import queue, retry
from chatelet.log import log

routes = web.RouteTableDef()

if config.EAGER_QUEUES:
    import nest_asyncio
    nest_asyncio.apply()


async def validate_intent(sub):
    async with ClientSession(raise_for_status=True, timeout=ClientTimeout(total=15)) as client:
        log.debug("Validating intent for %s (%s)", sub.url, sub.id)
        res = await client.post(sub.url, json={"intention": "pure"}, headers={
            "x-hook-secret": sub.secret
        })
        if res.ok and res.headers.get('x-hook-secret') == sub.secret:
            sub = await Subscription.get(sub.id)
            await sub.update(active=True).apply()
            log.debug("Intent validated for %s (%s)", sub.url, sub.id)
        else:
            raise ValueError(f"Intent _not_ validated for {sub.url} ({sub.id})")


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
                "headers": {
                    "x-hook-secret": {
                        "description": "The secret to use for validation of intent",
                        "type": "uuid",
                    }
                }
            },
            200: {
                "schema": schemas.AddSubscriptionResponse(),
                "description": "Subscription already exists",
            },
            403: {"description": "The url domain is not in accept list"},
            404: {"description": "Not found"},
            422: {"description": "Validation error"},
        },
    )
    @request_schema(schemas.AddSubscription())
    async def post(self):
        data = self.request["data"]

        sub = Subscription.query
        # TODO: handle a list of subscriptable events
        sub = sub.where(Subscription.event == data["event"])
        sub = sub.where(Subscription.url == data["url"])
        if "event_filter" in data:
            sub = sub.where(Subscription.event_filter == data["event_filter"])
        sub = await sub.gino.first()
        if sub:
            return web.json_response(sub.to_dict(), status=200)

        parsed = urlparse(data["url"])
        if not any([parsed.netloc.endswith(d) for d in config.ALLOWED_DOMAINS]):
            raise web.HTTPForbidden()

        data["active"] = not config.VALIDATION_OF_INTENT
        data["secret"] = str(uuid4())
        sub = await Subscription.create(**data)
        if config.VALIDATION_OF_INTENT and config.VALIDATION_OF_INTENT_IMMEDIATE:
            queue().enqueue(validate_intent, sub, retry=retry)
        return web.json_response(sub.to_dict(), status=201)


@docs(
    tags=["subscribe"],
    summary="Validate intent of a subscription",
    responses={
        200: {
            "description": "Subscription validated",
        },
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
    },
)
@headers_schema(schemas.HookSecretSchema)
@routes.post(r"/subscriptions/{id:\d+}/activate/")
async def activate_subscription(request):
    """Delayed validation of intent"""
    sub_id = int(request.match_info["id"])
    sub = await Subscription.get(sub_id)
    if not sub:
        raise web.HTTPNotFound()
    if request.headers.get('x-hook-secret') == sub.secret:
        await sub.update(active=True).apply()
        log.debug("Intent validated for %s (%s)", sub.url, sub.id)
        return web.json_response({"ok": True})
    else:
        log.debug("Failed intent validation for %s (%s)", sub.url, sub.id)
        raise web.HTTPUnprocessableEntity(reason="Hook secret not matched")


async def dispatch(subscription, data):
    # NB: using a new ClientSession for each dispatch is suboptimal
    # but how to reuse a session in worker threads?
    async with ClientSession(raise_for_status=True, timeout=ClientTimeout(total=15)) as client:
        log.debug("Dispatching %s to %s (%s)",
                  subscription.event, subscription.url, subscription.id)
        if subscription.event_filter:
            q = Path.parse_str(subscription.event_filter).match(data["payload"])
            if not list(q):
                log.debug("Skipped because of event filter: %s", subscription.event_filter)
                return
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
                # dummy to document the dispatch payload
                "schema": schemas.DispatchEvent(),
            },
            404: {"description": "Not found"},
            422: {"description": "Validation error"},
        },
    )
    @request_schema(schemas.AddPublication())
    async def post(self):
        data = await self.request.json()
        log.debug("Publishing: %s", data)
        subs = Subscription.query\
            .where(Subscription.event == data["event"])\
            .where(Subscription.active == True)  # noqa
        for sub in await subs.gino.all():
            queue().enqueue(dispatch, sub, data, retry=retry)
        raise web.HTTPCreated()


def api_factory():
    api = web.Application()
    api.add_routes(routes)
    api.middlewares.append(validation_middleware)
    setup_aiohttp_apispec(
        app=api,
        title="chatelet API",
        version="v1",
        url="/docs/swagger.json",
        swagger_path="/docs/",
    )
    return api
