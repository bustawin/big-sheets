from __future__ import annotations

import typing as t
from collections import defaultdict

import punq

from bigsheets.adapters.sheets import sheets
from bigsheets.adapters.ui import ui_port
from bigsheets.adapters.ui.gui import gui
from bigsheets.domain import command
from bigsheets.service import (
    command_handlers,
    event_handlers,
    message_bus,
    read_model, unit_of_work,
)


class BigSheets:
    def __init__(
        self,
        UI: t.Type[ui_port.UIPort] = gui.GUIAdapter,
        engine_factory: callable = sheets.engine_factory,
    ):
        """Bootstraps the app."""
        self.container = bootstrap(UI=UI, engine_factory=engine_factory)
        self.message_bus: message_bus.MessageBus = self.container.resolve(
            message_bus.MessageBus
        )
        self.ui: ui_port.UIPort = self.container.resolve(ui_port.UIPort)

    def start(self):
        self.ui.start(self._start_message_bus)

    def _start_message_bus(self):
        self.message_bus.start(
            self.container.resolve("event_handlers"),
            self.container.resolve("command_handlers"),
        )
        self.message_bus.handle(command.AskUserForASheet())


def bootstrap(
    engine_factory: callable,
    Uow: t.Type[unit_of_work.UnitOfWork] = unit_of_work.UnitOfWork,
    UI: t.Type[ui_port.UIPort] = gui.GUIAdapter,
) -> punq.Container:
    container = punq.Container()
    container.register(read_model.ReadModel, scope=punq.Scope.singleton)
    container.register(
        unit_of_work.UnitOfWork,
        Uow,
        scope=punq.Scope.singleton,
        sheet_engine_factory=engine_factory,
        Sheets=sheets.SheetsAdaptor,
    )
    container.register(ui_port.UIPort, UI, scope=punq.Scope.singleton)
    container.register(
        message_bus.MessageBus, scope=punq.Scope.singleton,
    )
    bootstrap_handlers("event_handlers", container, event_handlers.HANDLERS)
    bootstrap_handlers("command_handlers", container, command_handlers.HANDLERS)
    return container


def bootstrap_handlers(name, container: punq.Container, origin):
    """Registers the handlers in the containers so they can be
    used by the message bus.
    """
    final: message_bus.Handlers = defaultdict(set)
    for Handler in origin:
        for Message in Handler.HANDLES:
            final[Message].add(container.register(Handler).resolve(Handler))
    container.register(name, instance=final)
