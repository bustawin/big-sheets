from __future__ import annotations

import json
import typing as t

import webview


class Controller:
    variable: str = None

    def __init__(self, window: webview.Window):
        self.window = window

    def _exec(self, function: t.Union[str, callable], *args):
        fname = function.__name__ if callable(function) else function
        args = (json.dumps(arg) for arg in args)
        self.window.evaluate_js(f"{self.variable}.{fname}({','.join(args)})")


class Progress(Controller):
    variable = "progress"

    def start_processing(self, total: t.Optional[int] = None):
        self._exec("startProcessing", total)

    def update(self, completed):
        self._exec(self.update, completed)

    def finish(self):
        self._exec(self.finish)


class Info(Controller):
    variable = "info"

    def set(self, message):
        self._exec(self.set, message)

    def unset(self):
        self._exec(self.unset)


class Table(Controller):
    variable = "table"

    def set(self, rows: t.Collection, header: t.Collection):
        self._exec(self.set, rows, header)


class Query(Controller):
    variable = "query"

    def init(self, sheet_name: str, headers: t.List[str]):
        self._exec(self.init, sheet_name, headers)

    def set_message(self, message: str):
        self._exec("setMessage", message)

    def enable(self):
        self._exec(self.enable)

    def disable(self):
        self._exec(self.disable)


class Nav(Controller):
    variable = "nav"

    def enable(self):
        self._exec(self.enable)

    def disable(self):
        self._exec(self.disable)


class SheetsButton(Controller):
    variable = "sheetsButton"

    def set(self, sheets: t.Collection[dict]):
        self._exec(self.set, sheets)
