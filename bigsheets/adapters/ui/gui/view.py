from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import wraps

from bigsheets.service.message_bus import MessageBus


def print_exception(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            raise

    return wrapped


@dataclass
class View:
    bus: MessageBus

    @print_exception
    def open(self):
        pass

    @print_exception
    def query(self, query: str, limit, page):
        # todo CQRS
        self.spreadsheet.query(query, limit, page)

    @print_exception
    def open_csv(self, file: str):
        pass
