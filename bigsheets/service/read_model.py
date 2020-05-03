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
        q = f"{q} LIMIT {limit} OFFSET {limit * page}"

        with self.uow.instantiate() as uowi:
            cursor: sqlite3.Cursor = uowi.session.execute(q)
            yield tuple(h[0] for h in cursor.description)
            for row in cursor:
                yield row
