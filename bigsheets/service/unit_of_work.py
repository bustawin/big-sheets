from __future__ import annotations

import sqlite3
import typing as t
from dataclasses import dataclass

from bigsheets.adapters.sheets import sheets
from bigsheets.domain import model as m
from bigsheets.service.message_bus import MessageBus


@dataclass
class UnitOfWork:
    sheet_engine_factory: callable
    bus: MessageBus
    Sheets: t.Type[sheets.SheetsPort]

    def instantiate(self) -> UnitOfWorkInstance:
        session = self.sheet_engine_factory()
        sheets = self.Sheets(session)
        return UnitOfWorkInstance(bus=self.bus, session=session, sheets=sheets)

    def handle_breaking_uow(self, *models: m.ModelWithEvent):
        """Submits the events of the model breaking the unit of work
        pattern.

        Try to always submit events when committing the uow instance,
        which is the regular flow.
        """
        # This is useful to update the status of an operation before
        # it is committed
        _handle(*models, bus=self.bus)


@dataclass
class UnitOfWorkInstance:
    bus: MessageBus
    session: sqlite3.Connection
    sheets: sheets.SheetsPort

    def commit(self, *models: m.ModelWithEvent):
        """Commit and, after, submit the events."""
        self.session.commit()
        _handle(*models, bus=self.bus)

    def __enter__(self):
        self.session.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session.in_transaction:
            self.session.rollback()
        self.session.close()


def _handle(*models: m.ModelWithEvent, bus: MessageBus):
    for model in models:
        while model.events:
            bus.handle(model.events.popleft())
