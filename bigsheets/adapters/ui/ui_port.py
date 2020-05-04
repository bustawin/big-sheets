from __future__ import annotations

import abc
import typing as t
from pathlib import Path

from bigsheets.domain import model
from bigsheets.service import read_model


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
    def start_opening_sheet(self, sheet: model.Sheet):
        raise NotImplementedError

    @abc.abstractmethod
    def update_sheet_opening(self, completed: int):
        raise NotImplementedError

    @abc.abstractmethod
    def sheet_opened(self, *opened_sheets: model.Sheet):
        raise NotImplementedError

    @abc.abstractmethod
    def sheet_removed(self, *sheet: model.Sheet):
        raise NotImplementedError
