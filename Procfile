web: gunicorn chatelet.app:app_factory --worker-class aiohttp.GunicornWebWorker
worker: rq worker --with-scheduler
release: alembic upgrade head
