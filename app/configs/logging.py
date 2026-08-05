import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    app_logger.propagate = False

    for handler in app_logger.handlers:
        if getattr(handler, "_blog_api_handler", False):
            handler.setLevel(level)
            return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler._blog_api_handler = True  # type: ignore[attr-defined]

    app_logger.addHandler(handler)
