from __future__ import annotations

import typing as t
from dataclasses import dataclass

from . import model


class Event:
    pass


@dataclass
class SheetOpened(Event):
    sheet: model.Sheet
    opened_sheets: t.Collection[model.Sheet]


@dataclass
class SheetRemoved(Event):
    remaining_sheets: t.Collection[model.Sheet]

# todo missing event for WorkspaceLoaded
# todo missing event for WorkspaceSaved
