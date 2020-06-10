from __future__ import annotations

import logging
import threading
import typing as t
from contextlib import suppress
from functools import partial
from threading import Thread

import webview as pywebview

import bigsheets.service.utils
from bigsheets.domain import command, sheet
from bigsheets.service import message_bus, read_model, running
# noinspection PyUnresolvedReferences
from . import utils
from .query import controller, query_window
from .warnings import warnings_window
from ..ui_port import Sheets, UIPort

log = logging.getLogger(__name__)


class GUIAdapter(UIPort):
    webview: pywebview = pywebview
    ctrl: controller = controller

    def __init__(self, reader: read_model.ReadModel, bus: message_bus.MessageBus):
        super().__init__(reader)
        self.windows: t.List[query_window.QueryWindow] = []
        self.bus = bus
        self.warnings_window: t.Optional[warnings_window.WarningsWindow] = None

    def start(self, on_loaded: callable):
        # todo should on_loaded be an event?
        assert not self.windows
        log.info("Creating window %s", len(self.windows))
        self.windows.append(
            query_window.QueryWindow(
                self,
                self.handle_closing_window,
                partial(self._execute_outside_main_thread, on_loaded),
            )
        )
        self.webview.start(debug=bigsheets.service.utils.debug())

    def ask_user_for_sheet(self):
        return self.windows[-1].ask_user_for_sheet()

    def start_opening_sheet(self, sheet: sheet.Sheet):
        self.windows[-1].start_opening_sheet(sheet)

    def update_sheet_opening(self, completed: int):
        self.windows[-1].update_sheet_opening(completed)

    def sheet_opened(self, *opened_sheets: sheet.Sheet):
        for window in self.windows:
            window.sheet_opened()
            window.set_open_sheets(*opened_sheets)

    def sheet_removed(self, *sheet: sheet.Sheet):
        for window in self.windows:
            window.set_open_sheets(*sheet)

    def handle_closing_window(self, window: query_window.QueryWindow):
        with suppress(ValueError):
            self.windows.remove(window)
        if not self.windows:
            running.exit()

    def _execute_outside_main_thread(self, on_loaded):
        # pywebview wants to be alone executing its event loop
        # in the main thread, so we need to move the rest of the
        # starting in a separate thread
        Thread(target=on_loaded, name="bootstrap").start()

    def open_window(self):
        """Opens a new window showing the table of """
        ev = threading.Event()
        log.info("Creating window %s", len(self.windows))
        window = query_window.QueryWindow(
            self, self.handle_closing_window, lambda: ev.set()
        )
        ev.wait()
        self.windows.append(window)
        return window

    def open_sheet(self):
        window = self.open_window()
        if not self.bus.handle(command.AskUserForASheetOrWorkspace()):
            window.close()
            self.handle_closing_window(window)

    # Saving workspace

    def save_workspace(self):
        if filepath := self.windows[0].file_dialog(save="workspace.bsw"):
            # todo should we take this in "start_saving_workspace?"
            queries = tuple(w.query for w in self.windows)
            self.bus.handle(command.SaveWorkspace(queries, filepath))

    def start_saving_workspace(self, sheets: Sheets):
        total = max(sheet.num_rows for sheet in sheets)
        for window in self.windows:
            window.start_blocking_process(
                total, "Some functionality is disabled until the workspace is saved."
            )

    def update_saving_workspace(self, quantity: int):
        for window in self.windows:
            window.update_blocking_process(quantity)

    def finish_saving_workspace(self):
        for window in self.windows:
            window.finish_blocking_process()

    def start_loading_workspace(self, sheets: Sheets):
        total = max(sheet.num_rows for sheet in sheets)
        self.windows[0].start_blocking_process(
            total, "Functionality is disabled until the workspace is loaded."
        )

    def update_loading_workspace(self, quantity):
        self.windows[0].update_blocking_process(quantity)

    def finish_loading_workspace(self, queries: t.Collection[str]):
        first_query = True
        for query in queries:
            if first_query:
                first_query = False
                self.windows[0].init_with_query(query)
                self.windows[0].finish_blocking_process()
            else:
                ev = threading.Event()
                window = query_window.QueryWindow(
                    self, self.handle_closing_window, lambda: ev.set()
                )
                ev.wait()
                self.windows.append(window)
                window.init_with_query(query)

    # Managing "Warnings" window

    def open_warnings_window(self):
        if not self.warnings_window:
            self.warnings_window = warnings_window.WarningsWindow(
                self, self._on_closing_warnings_window
            )

    def _on_closing_warnings_window(self):
        self.warnings_window = None
