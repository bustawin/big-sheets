from __future__ import annotations

import typing as t
from dataclasses import dataclass

from . import sheet


class Event:
    pass


@dataclass
class SheetOpened(Event):
    sheet: sheet.Sheet
    opened_sheets: t.Collection[sheet.Sheet]


@dataclass
class SheetRemoved(Event):
    remaining_sheets: t.Collection[sheet.Sheet]

# todo missing event for WorkspaceLoaded
# todo missing event for WorkspaceSaved
