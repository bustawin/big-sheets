from __future__ import annotations

import typing as t
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import webview as pywebview

import bigsheets.service.utils
from bigsheets.adapters.ui.gui import controller
from bigsheets.domain import model
from bigsheets.service import running
from bigsheets.service.message_bus import MessageBus
# noinspection PyUnresolvedReferences
from . import utils
from .view import View
from ..ui_port import UIPort


class GUIAdapter(UIPort):
    webview: pywebview = pywebview
    ctrl: controller = controller

    def __init__(self, bus: MessageBus):
        super().__init__(bus)
        self.windows: t.List[Window] = []
        self.bus = bus

    def start(self, on_loaded: callable):
        # todo should on_loaded be an event?
        assert not self.windows
        self.windows.append(
            Window(self.bus, self.webview, self.ctrl, self.handle_closing_window, on_loaded)
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


class Window:
    @dataclass
    class Ctrl:
        progress: controller.Progress
        info: controller.Info
        table: controller.Table
        query: controller.Query

    def __init__(
        self,
        bus: MessageBus,
        webview: pywebview,
        ctrl: controller,
        on_closing: callable,
        on_loaded: callable
    ):
        self._view = View(bus)
        self.webview = webview
        self.native_window = self.webview.create_window(
            "Bigsheets", "adapters/ui/gui/templates/index.html", js_api=self._view
        )
        self.native_window.closing += partial(on_closing, self)
        self.native_window.loaded += on_loaded
        self.ctrl = self.Ctrl(
            ctrl.Progress(self.native_window),
            ctrl.Info(self.native_window),
            ctrl.Table(self.native_window),
            ctrl.Query(self.native_window),
        )

    def ask_user_for_sheet(self) -> t.Optional[Path]:
        r = self.native_window.create_file_dialog(
            self.webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("CSV (*.csv;*.tsv)",),
        )
        return Path(r[0]) if r else None

    def start_opening_sheet(self, sheet: model.Sheet):
        self.ctrl.progress.start_processing(sheet.num_rows)
        self.ctrl.info.set("Opening...")
        self.ctrl.table.set(sheet.rows, sheet.header)
        self.ctrl.query.init(sheet.name, sheet.header)

    def update_sheet_opening(self, completed: int):
        self.ctrl.progress.update(completed)

    def sheet_opened(self):
        self.ctrl.progress.finish()
        self.ctrl.info.unset()
