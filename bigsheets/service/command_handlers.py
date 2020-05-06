from __future__ import annotations

from bigsheets.adapters.ui import ui_port
from bigsheets.domain import command, event
from bigsheets.service import message_bus, unit_of_work
from bigsheets.service.handler import Handler, Handlers


class OpenSheetSelector(Handler):
    HANDLES = {command.AskUserForASheet}

    def __init__(self, bus: message_bus.MessageBus, ui: ui_port.UIPort):
        self.ui = ui
        self.bus = bus

    def __call__(self, message: command.AskUserForASheet):
        if filepath := self.ui.ask_user_for_sheet():
            if filepath.suffix == ".bsw":
                self.bus.handle(command.LoadWorkspace(filepath))
            else:
                return self.bus.handle(command.OpenSheet(filepath))


class OpenSheet(Handler):
    HANDLES = {command.OpenSheet}

    def __init__(self, uow: unit_of_work.UnitOfWork, ui: ui_port.UIPort):
        self.uow = uow
        self.ui = ui

    def __call__(self, message: command.OpenSheet):
        with self.uow.instantiate() as uow:
            sheet = uow.sheets.open_sheet(
                message.filepath, self.initial_callback, self.callback,
            )
            uow.commit(event.SheetOpened(sheet, tuple(uow.sheets.get())))
        return sheet

    def initial_callback(self, sheets):
        self.ui.start_opening_sheet(sheets)

    def callback(self, sheet, quantity):
        self.ui.update_sheet_opening(quantity)


class RemoveSheet(Handler):
    HANDLES = {command.RemoveSheet}

    def __init__(self, uow: unit_of_work.UnitOfWork):
        self.uow = uow

    def __call__(self, message: command.RemoveSheet):
        with self.uow.instantiate() as uowi:
            removed_sheet = uowi.sheets.remove_sheet(name=message.name)
            uowi.commit(removed_sheet)


class ExportView(Handler):
    HANDLES = {command.ExportView}

    def __init__(self, uow: unit_of_work.UnitOfWork):
        self.uow = uow

    def __call__(self, message: command.ExportView):
        with self.uow.instantiate() as uowi:
            uowi.sheets.export_view(message.query, message.filepath)


class SaveWorkspace(Handler):
    HANDLES = {command.SaveWorkspace}

    def __init__(self, uow: unit_of_work.UnitOfWork, ui: ui_port.UIPort):
        self.uow = uow
        self.ui = ui

    def __call__(self, message: command.SaveWorkspace):
        with self.uow.instantiate() as uowi:
            uowi.sheets.save_workspace(
                message.queries, message.filepath, self.initial_callback, self.callback
            )
        self.ui.finish_saving_workspace()

    def initial_callback(self, sheets):
        self.ui.start_saving_workspace(sheets)

    def callback(self, quantity):
        self.ui.update_saving_workspace(quantity)


class LoadWorkspace(Handler):
    HANDLES = {command.LoadWorkspace}

    def __init__(self, uow: unit_of_work.UnitOfWork, ui: ui_port.UIPort):
        self.uow = uow
        self.ui = ui

    def __call__(self, message: command.LoadWorkspace):
        with self.uow.instantiate() as uowi:
            queries = uowi.sheets.load_workspace(
                message.filepath, self.initial_callback, self.callback
            )
            uowi.commit()
        self.ui.finish_loading_workspace(queries)

    def initial_callback(self, sheets):
        self.ui.start_loading_workspace(sheets)

    def callback(self, quantity):
        self.ui.update_loading_workspace(quantity)


HANDLERS: Handlers = {
    OpenSheet,
    OpenSheetSelector,
    RemoveSheet,
    ExportView,
    SaveWorkspace,
    LoadWorkspace,
}
