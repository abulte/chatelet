web: gunicorn chatelet.app:app_factory --worker-class aiohttp.GunicornWebWorker
worker: rq worker --with-scheduler --url $REDIS_URL
release: alembic upgrade head
