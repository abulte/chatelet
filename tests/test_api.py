import os
from unittest import mock

import pytest
import nest_asyncio

from aiohttp.test_utils import TestClient, TestServer
from aioresponses import aioresponses
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


@pytest.fixture()
async def subscription(client):
    return await client.post("/api/subscriptions/", json={
        "event": "event",
        "event_filter": "event_filter",
        "url": "http://example.com"
    })


async def test_add_subscription_not_access_list(client):
    resp = await client.post("/api/subscriptions/", json={
        "event": "event",
        "event_filter": "event_filter",
        "url": "http://nimportquoi.com"
    })
    assert resp.status == 403


async def test_add_subscription(client, subscription):
    # first one created by fixture
    assert subscription.status == 201

    resp = await client.post("/api/subscriptions/", json={
        "event": "event",
        "event_filter": "event_filter",
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


async def test_publish(client, rmock, subscription):
    """Publish an event and dispatch it to one subscriber"""
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
        "event_filter": "event_filter",
        "ok": True,
        "payload": payload,
        "subscription": 1
    }
