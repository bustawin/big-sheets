import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bigsheets.service import unit_of_work
from bigsheets.service.read_model import ReadModel

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def uow(engine_factory):
    return unit_of_work.UnitOfWork(
        sheet_engine_factory=engine_factory, bus=MagicMock(), Sheets=MagicMock()
    )


class TestQuery:
    def test_happy_path(self, uow):
        with uow.instantiate() as uowi:
            uowi.session.execute("create table sheet1(x numeric, y numeric)")
            uowi.session.execute("insert into sheet1 values (1, 2)")
            uowi.commit()

        r = ReadModel(uow).query("select * from sheet1", 10, 0)
        headers = next(r)
        assert headers == ("x", "y")
        rows = tuple(r)
        assert rows == ((1, 2),)

    def test_syntax_error(self, uow):
        """User input error."""
        with pytest.raises(sqlite3.OperationalError):
            tuple(ReadModel(uow).query("select 1- from sheet1", 1, 1))
