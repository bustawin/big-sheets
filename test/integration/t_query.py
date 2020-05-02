from pathlib import Path
from unittest.mock import MagicMock

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.mark.skip
def test_query():
    db = DBRepository()
    keep_alive = db.connect()
    db.process_spreadsheet(
        FIXTURES / "cities.csv", MagicMock(), MagicMock(), MagicMock()
    )
    result = MagicMock()
    db.query("select * from sheet1", 2, 1, result)
    result.assert_called_once_with(
        (
            ("42", "52", "48", "N", "97", "23", "23", "W", "Yankton", "SD"),
            ("46", "35", "59", "N", "120", "30", "36", "W", "Yakima", "WA"),
        ),
        ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"),
    )


@pytest.mark.skip
def test_q():
    db = DBRepository()
    keep_alive = db.connect()
    db.process_spreadsheet(
        FIXTURES / "cities.csv", MagicMock(), MagicMock(), MagicMock()
    )

    def foo(*args, **kwargs):
        db_name = args[0]

    db.query("explain select * from sheet1", 2, 1, foo, MagicMock())


@pytest.mark.skip
def test_table_name():
    db = DBRepository()
    keep_alive = db.connect()
    r = db._new_table_name(keep_alive)
    assert r == 'sheet1'
    keep_alive.execute('create table sheet1 (foo)')
    r = db._new_table_name(keep_alive)
    assert r == 'sheet2'
