from __future__ import annotations

from dataclasses import dataclass

from . import model


class Event:
    pass


@dataclass
class SheetOpened(Event):
    sheet: model
