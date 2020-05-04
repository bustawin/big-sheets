from __future__ import annotations

from bigsheets.adapters.ui import ui_port
from bigsheets.domain import event as e
from bigsheets.service.handler import Handler, Handlers


class UpdateUISheetOpened(Handler):
    HANDLES = {e.SheetOpened}

    def __init__(self, ui: ui_port.UIPort):
        self.ui = ui

    def __call__(self, message: e.SheetOpened):
        self.ui.sheet_opened(*message.opened_sheets)


class SheetRemoved(Handler):
    HANDLES = {e.SheetRemoved}

    def __init__(self, ui: ui_port.UIPort):
        self.ui = ui

    def __call__(self, message: e.SheetRemoved):
        self.ui.sheet_removed(*message.remaining_sheets)


HANDLERS: Handlers = {UpdateUISheetOpened, SheetRemoved}
