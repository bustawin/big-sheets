from __future__ import annotations

import logging
import threading
import typing as t
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import Thread

import webview as pywebview

import bigsheets.service.utils
from bigsheets.adapters.ui.gui import controller
from bigsheets.domain import command, model
from bigsheets.service import message_bus, read_model, running

# noinspection PyUnresolvedReferences
from . import utils
from .view import View
from ..ui_port import Sheets, UIPort

log = logging.getLogger(__name__)


class GUIAdapter(UIPort):
    webview: pywebview = pywebview
    ctrl: controller = controller

    def __init__(self, reader: read_model.ReadModel, bus: message_bus.MessageBus):
        super().__init__(reader)
        self.windows: t.List[Window] = []
        self.bus = bus

    def start(self, on_loaded: callable):
        # todo should on_loaded be an event?
        assert not self.windows
        log.info("Creating window %s", len(self.windows))
        self.windows.append(
            Window(
                self,
                self.handle_closing_window,
                partial(self._execute_outside_main_thread, on_loaded),
            )
        )
        self.webview.start(debug=bigsheets.service.utils.debug())

    def ask_user_for_sheet(self):
        return self.windows[-1].ask_user_for_sheet()

    def start_opening_sheet(self, sheet: model.Sheet):
        self.windows[-1].start_opening_sheet(sheet)

    def update_sheet_opening(self, completed: int):
        self.windows[-1].update_sheet_opening(completed)

    def sheet_opened(self, *opened_sheets: model.Sheet):
        for window in self.windows:
            window.sheet_opened()
            window.set_open_sheets(*opened_sheets)

    def sheet_removed(self, *sheet: model.Sheet):
        for window in self.windows:
            window.set_open_sheets(*sheet)

    def handle_closing_window(self, window: Window):
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
        window = Window(self, self.handle_closing_window, lambda: ev.set())
        ev.wait()
        self.windows.append(window)
        return window

    def open_sheet(self):
        window = self.open_window()
        if not self.bus.handle(command.AskUserForASheet()):
            window.close()
            self.handle_closing_window(window)

    # Saving workspace

    def save_workspace(self):
        if filepath := self.windows[0].file_dialog(save=True):
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
                window = Window(self, self.handle_closing_window, lambda: ev.set())
                ev.wait()
                self.windows.append(window)
                window.init_with_query(query)


class Window:
    @dataclass
    class Ctrl:
        progress: controller.Progress
        info: controller.Info
        table: controller.Table
        query: controller.Query
        nav: controller.Nav
        sheets_button: controller.SheetsButton

    def __init__(
        self, ui: GUIAdapter, on_closing: callable, on_loaded: callable,
    ):
        self.reader: read_model.ReadModel = ui.reader
        self._view = View(self.reader, None, ui, self, ui.bus)
        self.bus = ui.bus
        self.webview: pywebview = ui.webview
        self.native_window = self.webview.create_window(
            "Bigsheets", "adapters/ui/gui/templates/index.html", js_api=self._view
        )
        self.native_window.closing += partial(on_closing, self)
        self.native_window.closed += self._on_close
        self.native_window.loaded += lambda: log.info("Window created and loaded.")
        self.native_window.loaded += on_loaded
        self.ctrl = self.Ctrl(
            ui.ctrl.Progress(self.native_window),
            ui.ctrl.Info(self.native_window),
            ui.ctrl.Table(self.native_window),
            ui.ctrl.Query(self.native_window),
            ui.ctrl.Nav(self.native_window),
            ui.ctrl.SheetsButton(self.native_window),
        )
        self._view.ctrl = self.ctrl

    @property
    def query(self):
        return self.ctrl.query.query

    def ask_user_for_sheet(self) -> t.Optional[Path]:
        return self.file_dialog(save=False)

    def start_opening_sheet(self, sheet: model.Sheet):
        self.ctrl.progress.start_processing(sheet.num_rows)
        self.ctrl.info.set(
            "Some functionality is disabled until the sheet finishes opening."
        )
        self.ctrl.table.set(sheet.rows, sheet.header)
        self.ctrl.query.init(sheet.name, sheet.header)
        self.ctrl.query.disable()

    def update_sheet_opening(self, completed: int):
        self.ctrl.progress.update(completed)

    def sheet_opened(self):
        self.ctrl.progress.finish()
        self.ctrl.info.unset()
        self.ctrl.nav.enable()
        self.ctrl.query.enable()

    def init_with_query(self, query: t.Optional[str] = None):
        """ Initializes the window and executes the passed-in query.
        :param query: The query whose resulsts to show in the table.
                      If None, use a predefined query over the last
                      sheet.
        :return:
        """
        r = self.reader.query(query) if query else self.reader.q_default_last_sheet()
        headers = next(r)
        results = tuple(r)
        self.ctrl.table.set(results, headers)
        self.ctrl.query.init(
            "sheet1", headers
        )  # todo change by the name of all sheets!
        self.ctrl.nav.enable()
        self.ctrl.query.enable()
        self.set_open_sheets(*self.reader.opened_sheets())

    def set_open_sheets(self, *sheets: model.Sheet):
        self.ctrl.sheets_button.set(
            [{"name": sheet.name, "filename": sheet.filename} for sheet in sheets]
        )

    def close(self):
        self.native_window.destroy()  # Destroy does not trigger on_close

    def _on_close(self):
        # todo properly remove the window and view, etc from ram
        pass

    def export_view(self, query: str):
        if filepath := self.file_dialog(save=True):
            self.bus.handle(command.ExportView(query, filepath))

    def file_dialog(self, *, save: bool) -> t.Optional[Path]:
        r = self.native_window.create_file_dialog(
            self.webview.SAVE_DIALOG if save else self.webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("CSV and BigSheets (*.bsw;*.csv;*.tsv)",),
        )
        return Path(r[0]) if r else None

    def start_blocking_process(self, total: int, info: str):
        self.ctrl.nav.disable()
        self.ctrl.query.disable()
        self.ctrl.info.set(info)
        self.ctrl.progress.start_processing(total)

    def update_blocking_process(self, quantity: int):
        self.ctrl.progress.update(quantity)

    def finish_blocking_process(self):
        self.ctrl.progress.finish()
        self.ctrl.nav.enable()
        self.ctrl.query.enable()
        self.ctrl.info.unset()
