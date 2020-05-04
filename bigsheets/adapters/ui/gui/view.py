from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from functools import wraps

from bigsheets.service import read_model
from . import gui

log = logging.getLogger(__name__)


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
    reader: read_model.ReadModel
    ctrl: gui.Window.Ctrl
    ui: gui.GUIAdapter

    @print_exception
    def open(self):
        pass

    @print_exception
    def query(self, query: str, limit, page):
        try:
            r = self.reader.query(query, limit, page)
            headers = next(r)
            # for huge number of rows we could use simplejson to
            # avoid creating a tuple in memory
            results = tuple(r)
        except sqlite3.OperationalError as e:  # todo wrap error with db generic?
            log.info(f"Wrong query {e}")
            self.ctrl.query.set_message(str(e))
        else:
            self.ctrl.table.set(results, headers)

    @print_exception
    def open_window(self):
        self.ui.open_window()
