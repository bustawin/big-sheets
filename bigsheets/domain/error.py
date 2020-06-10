from __future__ import annotations

import abc

from bigsheets.domain import sheet as sheet_model


class Error(abc.ABC):
    """An error when opening a sheet"""

    def __init__(self, filename: str):
        self.filename = filename

    def dict(self) -> dict:
        d = vars(self)
        d["type"] = self.__class__.__name__
        return d

    def __hash__(self):
        return hash(self.filename)


class WrongRow(Error):
    def __init__(self, filename: str, sheet_name: str, row: sheet_model.Row):
        self.sheet_name = sheet_name
        self.row = row
        super().__init__(filename)


class OpeningFileFailed(Error):
    def __init__(self, filename: str, error: Exception):
        self.error = error
        super().__init__(filename)
