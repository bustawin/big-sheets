import locale
import logging
import logging.config
import logging.handlers
import sys
from pathlib import Path

import decouple


def debug() -> bool:
    return decouple.config("DEBUG", default=True, cast=bool)


def frozen() -> bool:
    """Whether we are running in a bundle."""
    return getattr(sys, "frozen", False)


def setup_logging():
    level = logging.DEBUG if debug() else logging.INFO
    config = {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s ; %(name)s ; %(levelname)s ; %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": level,
                "stream": "ext://sys.stderr",
            },
        },
        "root": {"level": level, "handlers": {"console"}},
    }
    if frozen():
        # todo this path is macOS specific
        filepath = Path.home() / "Library" / "Logs" / "com.bustawin.big-sheets"
        filepath.mkdir(exist_ok=True)
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "simple",
            "level": level,
            "filename": str(filepath / "big-sheets.log"),
            "maxBytes": 3 * 10 ** 6,
            "backupCount": 2,
        }
        config["root"]["handlers"] = {"file"}
    logging.config.dictConfig(config)
    logging.info(
        "Big Sheets %s %s",
        "frozen" if frozen() else "not frozen",
        "in debug mode" if debug() else "in NON-debug mode",
    )

    def log_unhandled_exceptions(*exc_info):
        logging.exception("Unhandled exception:", exc_info=exc_info)

    sys.excepthook = log_unhandled_exceptions


def ensure_utf8():
    """
    Python3 uses by default the system set, but it expects it to be
    ‘utf-8’ to work correctly.
    This can generate problems in reading and writing files and in
    ``.decode()`` method.

    An example how to 'fix' it::

        echo 'export LC_CTYPE=en_US.UTF-8' > .bash_profile
        echo 'export LC_ALL=en_US.UTF-8' > .bash_profile
    """
    encoding = locale.getpreferredencoding()
    if encoding.lower() != "utf-8":
        raise OSError(f"Your encoding is {encoding}. Must be UTF-8")
