import sqlite3
from unittest import mock
from unittest.mock import MagicMock

import pytest

from bigsheets.service.unit_of_work import UnitOfWork


def test_commit_happy_path():
    engine = lambda: mock.create_autospec(sqlite3.Connection)
    bus = MagicMock()
    Sheets = MagicMock()
    uow = UnitOfWork(engine, bus, Sheets, MagicMock())
    with uow.instantiate() as uowi:
        session = uowi.session

        def _side_effect():
            session.in_transaction = False

        session.commit = MagicMock(side_effect=_side_effect)
        assert isinstance(uowi.session, sqlite3.Connection)
        uowi.commit()
    session.rollback.assert_not_called()
    session.commit.assert_called_once()


@pytest.mark.skip(reason="Not developed.")
def test_commit_with_models_to_handle():
    pass
