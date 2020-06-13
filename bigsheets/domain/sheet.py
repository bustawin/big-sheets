from __future__ import annotations

import typing as t
from collections import deque

from . import event

Cell = t.Union[int, float, str, None]
Cells = Row = Column = t.List[Cell]
Rows = t.List[Row]


class ModelWithEvent(t.Protocol):
    events: t.Deque[event.Event]


class Sheet:
    """The root entity of the Sheet aggregate.

    Represents an opened sheet.
    """

    def __init__(
        self, name: str, rows: Rows, header: Row, num_rows: int, filename: str
    ):
        self.rows: Rows = rows
        """The rows of the sheet. For a sheet that is opening,
        the rows that all available at the moment.
        """
        # todo a sqlalchemy mapper should map this value to the adapter

        self.name: str = name
        """The name of the sheet, which is the name of the table too."""
        self.events: t.Deque[event.Event] = deque()
        self.num_rows: int = num_rows
        """The rows the sheet has, including wrong ones,
         even if not all are available yet.
         """
        self.header: Row = header
        self.filename = filename

    def __str__(self):
        return f"Sheet {self.name}"

    def __repr__(self):
        return f"<Sheet {self.name}>"

    def __hash__(self):
        return hash(self.name)

    def remove(self, remaining_sheets: t.Collection[Sheet]):
        self.events.append(event.SheetRemoved(remaining_sheets=remaining_sheets))


def new_sheet_name(number_of_sheets: int):
    return f"sheet{number_of_sheets + 1}"
