from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import webview as pywebview

# noinspection PyUnresolvedReferences
from bigsheets.adapters.ui.gui import gui, utils
from bigsheets.domain import command, model
from bigsheets.service import read_model
from . import controller
from .view import View

log = logging.getLogger(__name__)


class QueryWindow:
    @dataclass
    class Ctrl:
        progress: controller.Progress
        info: controller.Info
        table: controller.Table
        query: controller.Query
        nav: controller.Nav
        sheets_button: controller.SheetsButton

    def __init__(
        self, ui: gui.GUIAdapter, on_closing: callable, on_loaded: callable,
    ):
        self.reader: read_model.ReadModel = ui.reader
        self._view = View(self.reader, None, ui, self, ui.bus)
        self.bus = ui.bus
        self.webview: pywebview = ui.webview
        self.native_window = self.webview.create_window(
            "BigSheets", "adapters/ui/gui/web-files/query/index.html", js_api=self._view
        )
        self.on_closing = on_closing
        self.native_window.closing += partial(on_closing, self)
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

    @property
    def title(self):
        return self.native_window.title

    @title.setter
    def title(self, value):
        self.native_window.set_title(value)

    def ask_user_for_sheet(self) -> t.Optional[Path]:
        return self.file_dialog()

    def start_opening_sheet(self, sheet: model.Sheet):
        self.ctrl.progress.start_processing(sheet.num_rows)
        self.ctrl.info.set(
            "Some functionality is disabled until the sheet finishes opening."
        )
        self.ctrl.table.set(sheet.rows, sheet.header)
        self.ctrl.query.init(sheet.name)
        self.ctrl.query.disable()

    def update_sheet_opening(self, completed: int):
        self.ctrl.progress.update(completed)

    def sheet_opened(self):
        self.ctrl.progress.finish()
        self.unset_info()
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
        self.ctrl.query.init("sheet1")  # todo change by the name of all sheets!
        self.ctrl.nav.enable()
        self.ctrl.query.enable()
        self.set_open_sheets(*self.reader.opened_sheets())

    def set_open_sheets(self, *sheets: model.Sheet):
        self.ctrl.sheets_button.set(
            [{"name": sheet.name, "filename": sheet.filename} for sheet in sheets]
        )
        self.ctrl.query.set_opened_sheets(
            {sheet.name: sheet.header for sheet in sheets}
        )

    def close(self):
        self.on_closing(self)
        self.native_window.destroy()  # Destroy does not trigger closing, etc.

    def export_view(self, query: str):
        if filepath := self.file_dialog(save="sheet.csv"):
            self.bus.handle(command.ExportView(query, filepath))

    def file_dialog(self, *, save: t.Optional[str] = None) -> t.Optional[Path]:
        """Creates an open file dialog if save is falsy, and a save dialog when
        save is a string with an exemplifying filename.
        """
        r = self.native_window.create_file_dialog(
            self.webview.SAVE_DIALOG if save else self.webview.OPEN_DIALOG,
            allow_multiple=False,
            save_filename=save,
            file_types=("CSV and BigSheets (*.bsw;*.csv;*.tsv;*.tab)",),
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
        self.unset_info()

    def unset_info(self):
        if self.reader.errors():
            self.ctrl.info.set_warnings()
        else:
            self.ctrl.info.unset()
