from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from functools import wraps

from bigsheets.domain import command
from bigsheets.service import message_bus, read_model
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
    window: gui.Window
    bus: message_bus.MessageBus

    @print_exception
    def query(self, query: str, limit, page):
        self.window.title = query
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
        window = self.ui.open_window()
        window.init_with_query()

    @print_exception
    def close_window(self):
        self.window.close()

    @print_exception
    def remove_sheet(self, name: str):
        self.bus.handle(command.RemoveSheet(name))

    @print_exception
    def open_sheet(self):
        self.ui.open_sheet()

    @print_exception
    def export_view(self, query: str):
        self.window.export_view(query)

    @print_exception
    def save_workspace(self):
        self.ui.save_workspace()
