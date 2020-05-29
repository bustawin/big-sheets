from __future__ import annotations

import logging

import webview as pywebview

from bigsheets.adapters.ui.gui import gui

# noinspection PyUnresolvedReferences
from .view import View

log = logging.getLogger(__name__)


class WarningsWindow:
    def __init__(self, ui: gui.GUIAdapter, on_closing: callable):
        self.webview: pywebview = ui.webview
        self.native_window = self.webview.create_window(
            "Warnings — BigSheets",
            "adapters/ui/gui/web-files/warnings/warnings.html",
            js_api=View(ui.reader),
        )
        self.native_window.closing += on_closing

    def restore(self):
        self.native_window.restore()
