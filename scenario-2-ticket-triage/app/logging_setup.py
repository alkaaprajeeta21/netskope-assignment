import logging
import os
from pythonjsonlogger import jsonlogger

def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s %(operation)s %(latency_ms)s"
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]
