from rq import Queue, Retry
from redis import Redis

from chatelet import config

context = {}
redis_conn = Redis()
retry = Retry(max=3, interval=[10, 30, 60])


def queue():
    if "_queue" in context:
        return context["_queue"]
    context["_queue"] = Queue(connection=redis_conn, is_async=not config.EAGER_QUEUES)
    return context["_queue"]
