import logging
import sys

from chatelet import config


log = logging.getLogger("decapode")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
