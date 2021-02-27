import os
from functools import partial
from unittest import mock

import pytest
import nest_asyncio

from aiohttp.test_utils import TestClient, TestServer
from aioresponses import aioresponses, CallbackResult
from fakeredis import FakeStrictRedis
from yarl import URL

from chatelet.app import app_factory
from chatelet.app import db

nest_asyncio.apply()
pytestmark = pytest.mark.asyncio
DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/postgres"


# this really really really should run first (or "prod" db will get erased)
@pytest.fixture(autouse=True, scope="session")
def setup():
    with mock.patch.dict(os.environ, {"DATABASE_URL": DATABASE_URL}):
        yield


@pytest.fixture(autouse=True)
def setup_config(setup, mocker):
    mocker.patch("chatelet.config.ALLOWED_DOMAINS", ["example.com"])
    mocker.patch("chatelet.config.EAGER_QUEUES", True)
    mocker.patch("chatelet.config.VALIDATION_OF_INTENT", False)
    mocker.patch("chatelet.queue.redis_conn", FakeStrictRedis())


@pytest.fixture(autouse=True)
async def client(setup_config):
    app = app_factory()
    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.fixture(autouse=True)
async def clean_db(client):
    await db.gino.create_all()
    yield
    await db.gino.drop_all()


@pytest.fixture
def rmock():
    # passthrough for local requests (aiohttp TestServer)
    with aioresponses(passthrough=["http://127.0.0.1"]) as m:
        yield m


@pytest.fixture
async def subscription(client):
    async def create(**kwargs):
        return await client.post("/api/subscriptions/", json=kwargs)
    return partial(create, event="event", url="http://example.com")


async def test_add_subscription_not_access_list(client):
    resp = await client.post("/api/subscriptions/", json={
        "event": "event",
        "url": "http://nimportquoi.com"
    })
    assert resp.status == 403


async def test_add_subscription(client, subscription):
    sub = await subscription()
    assert sub.status == 201

    resp = await client.post("/api/subscriptions/", json={
        "event": "event",
        "url": "http://example.com"
    })
    assert resp.status == 200

    resp = await client.get("/api/subscriptions/")
    assert resp.status == 200
    assert len(await resp.json()) == 1


async def test_add_subscription_error(client):
    resp = await client.post("/api/subscriptions/", json={})
    assert resp.status == 422
    data = await resp.json()
    assert all([e in data for e in ["url", "event"]])

    resp = await client.post("/api/subscriptions/", json={
        "event": "event",
        "url": "notanurl"
    })
    assert resp.status == 422
    assert "url" in await resp.json()

    resp = await client.post("/api/subscriptions/", json={
        "event": "event",
        "event_filter": "notajsonpath",
        "url": "http://example.com",
    })
    assert resp.status == 422
    assert "event_filter" in await resp.json()


async def test_publish(client, rmock, subscription):
    """Publish an event and dispatch it to one subscriber"""
    await subscription()
    rmock.post("http://example.com")
    payload = {
        "hop": "la",
        "oops": {"ta": "da"},
    }
    resp = await client.post("/api/publications/", json={
        "event": "event",
        "payload": payload,
    })
    assert resp.status == 201
    rkey = ("POST", URL("http://example.com"))
    assert rkey in rmock.requests
    r = rmock.requests[rkey]
    assert r[0].kwargs["json"] == {
        "event": "event",
        "event_filter": None,
        "ok": True,
        "payload": payload,
        "subscription": 1
    }


async def test_publish_event_filter_ok(client, rmock, subscription):
    """Publish an event and dispatch it to one subscriber"""
    rmock.post("http://example.com")
    sub = await subscription(event_filter='$[?(@.hop = "la")]')
    assert sub.status == 201
    payload = {
        "hop": "la",
        "oops": {"ta": "da"},
    }
    resp = await client.post("/api/publications/", json={
        "event": "event",
        "payload": payload,
    })
    assert resp.status == 201
    rkey = ("POST", URL("http://example.com"))
    assert rkey in rmock.requests


async def test_publish_event_filter_ko(client, rmock, subscription):
    """Publish an event and do _not_ dispatch it to one subscriber"""
    sub = await subscription(event_filter='$[?(@.hop = "NOT")]')
    rmock.post("http://example.com")
    payload = {
        "hop": "la",
        "oops": {"ta": "da"},
    }
    assert sub.status == 201
    resp = await client.post("/api/publications/", json={
        "event": "event",
        "payload": payload,
    })
    assert resp.status == 201
    rkey = ("POST", URL("http://example.com"))
    assert rkey not in rmock.requests


async def test_validation_of_intent_not_done(client, rmock, mocker, subscription):
    """Publish an event and do _not_ dispatch it to one subscriber"""
    mocker.patch("chatelet.config.VALIDATION_OF_INTENT", True)
    rmock.post("http://example.com")
    await subscription()
    resp = await client.post("/api/publications/", json={
        "event": "event",
        "payload": {},
    })
    assert resp.status == 201
    rkey = ("POST", URL("http://example.com"))
    assert rkey in rmock.requests
    r = rmock.requests[rkey]
    assert len(r) == 1
    assert r[0].kwargs["json"] == {"intention": "pure"}


async def test_validation_of_intent_done(client, rmock, mocker, subscription):
    """Publish an event and dispatch it to one subscriber"""
    mocker.patch("chatelet.config.VALIDATION_OF_INTENT", True)

    # validation of intent
    def callback(_, **kwargs):
        secret = kwargs["headers"].get("x-hook-secret")
        return CallbackResult(status=200, headers={"x-hook-secret": secret})
    rmock.post("http://example.com", callback=callback)
    await subscription()

    rmock.post("http://example.com")
    resp = await client.post("/api/publications/", json={
        "event": "event",
        "payload": {},
    })
    assert resp.status == 201
    rkey = ("POST", URL("http://example.com"))
    assert rkey in rmock.requests
    r = rmock.requests[rkey]
    assert len(r) == 2
    assert r[0].kwargs["json"] == {"intention": "pure"}
    assert "payload" in r[1].kwargs["json"]
