from __future__ import annotations

import abc
import typing as t
from pathlib import Path

from bigsheets.domain import sheet
from bigsheets.service import read_model

Sheets = t.Collection[sheet.Sheet]


class UIPort(abc.ABC):
    """The primary actor for the user interface using the presenter
    pattern.

    Internally uses the GUI xor CLI, depending of the environment.
    """

    def __init__(self, reader: read_model.ReadModel):
        self.reader = reader

    @abc.abstractmethod
    def start(self, on_loaded: callable):
        raise NotImplementedError

    @abc.abstractmethod
    def ask_user_for_sheet(self) -> t.Optional[Path]:
        raise NotImplementedError

    @abc.abstractmethod
    def start_opening_sheet(self, sheet: sheet.Sheet):
        raise NotImplementedError

    @abc.abstractmethod
    def update_sheet_opening(self, completed: int):
        raise NotImplementedError

    @abc.abstractmethod
    def sheet_opened(self, opened_sheets: sheet.Sheet):
        raise NotImplementedError

    @abc.abstractmethod
    def sheet_removed(self, *sheet: sheet.Sheet):
        raise NotImplementedError

    @abc.abstractmethod
    def open_sheet(self):
        raise NotImplementedError

    @abc.abstractmethod
    def save_workspace(self):
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def start_saving_workspace(self, sheets: Sheets):
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def update_saving_workspace(self, quantity: int):
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def finish_saving_workspace(self):
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def start_loading_workspace(self, sheets: Sheets):
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def update_loading_workspace(self, quantity):
        """"""
        raise NotImplementedError

    @abc.abstractmethod
    def finish_loading_workspace(self, queries: t.Collection[str]):
        """"""
        raise NotImplementedError
