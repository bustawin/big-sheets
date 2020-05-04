from __future__ import annotations

import sqlite3
import typing as t
from dataclasses import dataclass

from bigsheets.domain import model
from bigsheets.service import unit_of_work


@dataclass
class ReadModel:
    """Queries the database as part of the CQRS
    (Command Query Responsibility Separation).
    """

    uow: unit_of_work.UnitOfWork

    def query(
        self, q: str, limit: int, page: int
    ) -> t.Iterator[t.Union[t.Tuple[str, ...], model.Row]]:
        with self.uow.instantiate() as uowi:
            for row in self._query(q, limit, page, uowi.session):
                yield row

    def query_default_last_sheet(self):
        with self.uow.instantiate() as uowi:
            sheet_name = f"sheet{uowi.sheets.number_of_sheets()}"
            q = f"SELECT * FROM {sheet_name}"
            yield sheet_name
            yield self._query(q, 50, 0, uowi.session)

    def _query(
        self, q: str, limit: int, page: int, session: sqlite3.Connection
    ) -> t.Iterator[t.Union[t.Tuple[str, ...], model.Row]]:
        q = f"{q} LIMIT {limit} OFFSET {limit * page}"

        cursor: sqlite3.Cursor = session.execute(q)
        yield tuple(h[0] for h in cursor.description)
        for row in cursor:
            yield row

    def opened_sheets(self):
        with self.uow.instantiate() as uowi:
            return uowi.sheets.get()
