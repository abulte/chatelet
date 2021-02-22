from rq import Queue, Retry
from redis import Redis

from chatelet import config

redis_conn = Redis()
queue = Queue(connection=redis_conn, is_async=not config.EAGER_QUEUES)
retry = Retry(max=3, interval=[10, 30, 60])
