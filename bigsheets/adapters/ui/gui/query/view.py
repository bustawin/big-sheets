from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from functools import wraps

from bigsheets.domain import command
from bigsheets.service import message_bus, read_model
from bigsheets.adapters.ui.gui import gui, utils as gui_utils
from . import query_window, controller
log = logging.getLogger(__name__)



@dataclass
class View:
    reader: read_model.ReadModel
    ctrl: query_window.QueryWindow.Ctrl
    ui: gui.GUIAdapter
    window: query_window.QueryWindow
    bus: message_bus.MessageBus

    @gui_utils.log_exception
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

    @gui_utils.log_exception
    def open_window(self):
        window = self.ui.open_window()
        window.init_with_query()

    @gui_utils.log_exception
    def close_window(self):
        self.window.close()

    @gui_utils.log_exception
    def remove_sheet(self, name: str):
        self.bus.handle(command.RemoveSheet(name))

    @gui_utils.log_exception
    def open_sheet(self):
        self.ui.open_sheet()

    @gui_utils.log_exception
    def export_view(self, query: str):
        self.window.export_view(query)

    @gui_utils.log_exception
    def save_workspace(self):
        self.ui.save_workspace()

    @gui_utils.log_exception
    def open_warnings(self):
        self.ui.open_warnings_window()
