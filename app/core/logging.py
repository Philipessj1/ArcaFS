import json
import logging
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger("arcafs")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)


def log_event(
        event: str,
        **kwargs: Any,
) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **kwargs,
    }

    logger.info(json.dumps(payload, default=str))
    