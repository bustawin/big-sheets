from __future__ import annotations

import typing as t
from collections import defaultdict

from bigsheets.adapters.sheets import sheets
from bigsheets.adapters.errors import errors as error_adapter
from bigsheets.adapters.ui import ui_port
from bigsheets.adapters.ui.gui import gui
from bigsheets.domain import command
from bigsheets.service import (
    command_handlers,
    event_handlers,
    message_bus,
    read_model,
    unit_of_work,
)
from bigsheets.adapters.container import Container, Scope


class BigSheets:
    def __init__(
        self,
        UI: t.Type[ui_port.UIPort] = gui.GUIAdapter,
        engine_factory: callable = sheets.engine_factory,
    ):
        """Bootstraps the app."""
        self.container = bootstrap(UI=UI, engine_factory=engine_factory)
        self.bus: message_bus.MessageBus = self.container.resolve(
            message_bus.MessageBus
        )
        self.ui: ui_port.UIPort = self.container.resolve(ui_port.UIPort)

    def start(self):
        self.ui.start(self._start_message_bus)

    def _start_message_bus(self):
        self.bus.start(
            self.container.resolve("event_handlers"),
            self.container.resolve("command_handlers"),
        )
        self.bus.handle(command.AskUserForASheetOrWorkspace())


def bootstrap(
    engine_factory: callable,
    Uow: t.Type[unit_of_work.UnitOfWork] = unit_of_work.UnitOfWork,
    UI: t.Type[ui_port.UIPort] = gui.GUIAdapter,
) -> Container:
    container = Container()
    container.register(read_model.ReadModel, scope=Scope.singleton)
    container.register(
        error_adapter.Errors, error_adapter.ErrorsAdapter, scope=Scope.singleton
    )
    container.register(
        unit_of_work.UnitOfWork,
        Uow,
        scope=Scope.singleton,
        sheet_engine_factory=engine_factory,
        Sheets=sheets.SheetsAdaptor,
    )
    container.register(ui_port.UIPort, UI, scope=Scope.singleton)
    container.register(
        message_bus.MessageBus, scope=Scope.singleton,
    )
    bootstrap_handlers("event_handlers", container, event_handlers.HANDLERS)
    bootstrap_handlers("command_handlers", container, command_handlers.HANDLERS)
    return container


def bootstrap_handlers(name, container: Container, origin):
    """Registers the handlers in the containers so they can be
    used by the message bus.
    """
    final: message_bus.Handlers = defaultdict(set)
    for Handler in origin:
        for Message in Handler.HANDLES:
            final[Message].add(container.register(Handler).resolve(Handler))
    container.register(name, instance=final)
