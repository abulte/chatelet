import os

from aiohttp import web

from chatelet.api import api
from chatelet.db import db

app = web.Application(middlewares=[db])
db.init_app(app, {
    "dsn": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
})
app.add_subapp("/api/", api)
