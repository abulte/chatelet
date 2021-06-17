import os

from aiohttp import web

from chatelet.api import api_factory
from chatelet.db import db


async def app_factory():
    app = web.Application(middlewares=[db])
    db.init_app(app, {
        "dsn": os.getenv("DATABASE_URL")
    })
    app.add_subapp("/api/", api_factory())
    return app


if __name__ == "__main__":
    web.run_app(app_factory())
