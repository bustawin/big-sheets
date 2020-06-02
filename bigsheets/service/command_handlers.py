from __future__ import annotations

import typing as t

from bigsheets.adapters.sheets import sheets as sheets_adapter
from bigsheets.adapters.ui import ui_port
from bigsheets.domain import command, event, model
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

    class Update(sheets_adapter.UpdateHandler):
        def __init__(self, ui: ui_port.UIPort):
            super().__init__()
            self.ui = ui

        def on_init(self, sheet: model.Sheet):
            super().on_init(sheet)
            self.ui.start_opening_sheet(sheet)

        def on_it(self, n: int):
            super().on_it(n)
            self.ui.update_sheet_opening(self.total)

    def __init__(self, uow: unit_of_work.UnitOfWork, ui: ui_port.UIPort):
        self.uow = uow
        self.ui = ui

    def __call__(self, message: command.OpenSheet):
        with self.uow.instantiate() as uow:
            sheet, wrong_rows = uow.sheets.open_sheet(
                message.filepath, update_handler=self.Update(self.ui)
            )
            uow.errors.add(*wrong_rows)
            uow.commit(event.SheetOpened(sheet, tuple(uow.sheets.get())))
        return sheet


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

    class Update(sheets_adapter.UpdateHandler):
        def __init__(self, ui: ui_port.UIPort):
            super().__init__()
            self.ui = ui

        def on_init(self, sheet: t.Collection[model.Sheet]):
            super().on_init(sheet)
            self.ui.start_saving_workspace(sheet)

        def on_it(self, n: int):
            super().on_it(n)
            if self.total % 10 == 0:
                # Update progress every 10th row for performance
                self.ui.update_saving_workspace(self.total)

    def __init__(self, uow: unit_of_work.UnitOfWork, ui: ui_port.UIPort):
        self.uow = uow
        self.ui = ui

    def __call__(self, message: command.SaveWorkspace):
        with self.uow.instantiate() as uowi:
            uowi.sheets.save_workspace(
                message.queries, message.filepath, update_handler=self.Update(self.ui)
            )
        self.ui.finish_saving_workspace()


class LoadWorkspace(Handler):
    HANDLES = {command.LoadWorkspace}

    class Update(sheets_adapter.UpdateHandler):
        def __init__(self, ui: ui_port.UIPort):
            super().__init__()
            self.ui = ui

        def on_init(self, sheet: t.Collection[model.Sheet]):
            super().on_init(sheet)
            self.ui.start_loading_workspace(sheet)

        def on_it(self, n: int):
            super().on_it(n)
            self.ui.update_loading_workspace(self.total)

    def __init__(self, uow: unit_of_work.UnitOfWork, ui: ui_port.UIPort):
        self.uow = uow
        self.ui = ui

    def __call__(self, message: command.LoadWorkspace):
        with self.uow.instantiate() as uowi:
            queries = uowi.sheets.load_workspace(
                message.filepath, update_handler=self.Update(self.ui)
            )
            uowi.commit()
        self.ui.finish_loading_workspace(queries)


HANDLERS: Handlers = {
    OpenSheet,
    OpenSheetSelector,
    RemoveSheet,
    ExportView,
    SaveWorkspace,
    LoadWorkspace,
}
