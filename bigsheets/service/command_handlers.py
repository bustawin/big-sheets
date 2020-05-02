from __future__ import annotations

from bigsheets.adapters.ui import ui_port
from bigsheets.domain import command
from bigsheets.service import message_bus, unit_of_work
from bigsheets.service.handler import Handler, Handlers


class OpenSheetSelector(Handler):
    HANDLES = {command.AskUserForASheet}

    def __init__(self, bus: message_bus.MessageBus, ui: ui_port.UIPort):
        self.ui = ui
        self.bus = bus

    def __call__(self, message: command.AskUserForASheet):
        if filepath := self.ui.ask_user_for_sheet():
            self.bus.handle(command.OpenSheet(filepath))


class OpenSheet(Handler):
    HANDLES = {command.OpenSheet}

    def __init__(self, uow: unit_of_work.UnitOfWork, ui: ui_port.UIPort):
        self.uow = uow
        self.time_to_die = False
        self.ui = ui

    def __call__(self, message: command.OpenSheet):
        with self.uow.instantiate() as uow:
            sheet = uow.sheets.open_sheet(
                message.filepath, self.initial_callback, self.callback,
            )
            uow.commit(sheet)
        return sheet

    def initial_callback(self, sheet):
        self.ui.start_opening_sheet(sheet)

    def callback(self, sheet, quantity):
        self.ui.update_sheet_opening(quantity)


HANDLERS: Handlers = {OpenSheet, OpenSheetSelector}
