from __future__ import annotations

import threading
import typing as t
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import Thread

import webview as pywebview

import bigsheets.service.utils
from bigsheets.adapters.ui.gui import controller
from bigsheets.domain import model
from bigsheets.service import read_model, running
# noinspection PyUnresolvedReferences
from . import utils
from .view import View
from ..ui_port import UIPort


class GUIAdapter(UIPort):
    webview: pywebview = pywebview
    ctrl: controller = controller

    def __init__(self, reader: read_model.ReadModel):
        super().__init__(reader)
        self.windows: t.List[Window] = []

    def start(self, on_loaded: callable):
        # todo should on_loaded be an event?
        assert not self.windows
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

    def sheet_opened(self):
        self.windows[-1].sheet_opened()

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
        window = Window(self, self.handle_closing_window, lambda: ev.set())
        ev.wait()
        self.windows.append(window)
        window.init_with_sheet()


class Window:
    @dataclass
    class Ctrl:
        progress: controller.Progress
        info: controller.Info
        table: controller.Table
        query: controller.Query
        nav: controller.Nav

    def __init__(
        self, ui: GUIAdapter, on_closing: callable, on_loaded: callable,
    ):
        self.reader: read_model.ReadModel = ui.reader
        self._view = View(self.reader, None, ui)
        self.webview: pywebview = ui.webview
        self.native_window = self.webview.create_window(
            "Bigsheets", "adapters/ui/gui/templates/index.html", js_api=self._view
        )
        self.native_window.closing += partial(on_closing, self)
        self.native_window.loaded += on_loaded
        self.ctrl = self.Ctrl(
            ui.ctrl.Progress(self.native_window),
            ui.ctrl.Info(self.native_window),
            ui.ctrl.Table(self.native_window),
            ui.ctrl.Query(self.native_window),
            ui.ctrl.Nav(self.native_window)
        )
        self._view.ctrl = self.ctrl

    def ask_user_for_sheet(self) -> t.Optional[Path]:
        r = self.native_window.create_file_dialog(
            self.webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("CSV (*.csv;*.tsv)",),
        )
        return Path(r[0]) if r else None

    def start_opening_sheet(self, sheet: model.Sheet):
        self.ctrl.progress.start_processing(sheet.num_rows)
        self.ctrl.info.set("Some functionality is disabled until the sheet finishes opening.")
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

    def init_with_sheet(self):
        r = self.reader.query_default_last_sheet()
        sheet_name = next(r)
        res = next(r)
        headers = next(res)
        results = tuple(res)
        self.ctrl.table.set(results, headers)
        self.ctrl.query.init(sheet_name, headers)
        self.ctrl.nav.enable()
        self.ctrl.query.enable()
