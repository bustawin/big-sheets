import csv
import io
import json
import tempfile
import zipfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, call

import pytest

from bigsheets.adapters.sheets.sheets import SheetsAdaptor, UpdateHandler
from bigsheets.domain import sheet as sheet_model
from bigsheets.domain.error import WrongRow
from test.conftest import FIXTURES


class TestSheets:
    @pytest.fixture
    def update_handler(self):
        UOSH = mock.create_autospec(UpdateHandler)
        return UOSH()

    def test_open_sheet(self, engine_factory, update_handler):
        e = engine_factory()

        sheet, errors = SheetsAdaptor(e).open_sheet(
            FIXTURES / "cities.csv", update_handler=update_handler
        )
        # Check sheet object
        assert sheet.name == "sheet1"
        assert sheet.num_rows == 128
        assert sheet.rows
        assert not errors

        # Check callbacks
        update_handler.on_init.assert_called_once_with(sheet)
        update_handler.on_it.assert_has_calls([call(99), call(99)])

        # Check db
        x = e.execute("SELECT * FROM sheet1 LIMIT 1")
        assert next(x) == (41, 5, 59, "N", 80, 39, 0, "W", "Youngstown", "OH")

    def test_open_sheet_wrong_rows(self, engine_factory, update_handler):
        e = engine_factory()
        sheet, errors = SheetsAdaptor(e).open_sheet(
            FIXTURES / "cities-wrong.csv", update_handler=update_handler
        )
        assert len(errors) == 1
        e = errors[0]
        assert e.filename.endswith('cities-wrong.csv')
        assert e.sheet_name == 'sheet1'
        assert e.row == ['41', '5', '59', 'N', '80', '39', '0', 'W', 'Youngstown']
        assert isinstance(e, WrongRow)

    def test_engine_persistance(self, engine_factory):
        session = engine_factory()
        with session:
            session.execute("create table s1(x numeric)")
            session.execute("insert into s1 values(1)")
            session.commit()
        # Close session and open a new one
        new_session = engine_factory()
        with new_session:
            result = tuple(new_session.execute("select * from s1"))
            assert result[0][0] == 1

    def test_export_view(self, engine_factory):
        session = engine_factory()
        with session, tempfile.NamedTemporaryFile(mode="w+") as fp:
            session.execute("create table s1(x numeric, y numeric)")
            session.execute('insert into s1 values("foo", "bar")')
            SheetsAdaptor(session).export_view("select * from s1", Path(fp.name))
            fp.seek(0)
            reader = csv.reader(fp)
            headers = next(reader)
            assert headers == ["x", "y"]
            row = next(reader)
            assert row == ["foo", "bar"]

    def test_save_workspace(self, engine_factory, MockedSheetsAdaptor, update_handler):
        session = engine_factory()

        with session, tempfile.NamedTemporaryFile(mode="wb+") as fp:
            session.execute("create table s1(x numeric, y numeric)")
            session.execute('insert into s1 values("foo", "bar")')
            sheet = sheet_model.Sheet(
                "s1", [], header=["x", "y"], num_rows=1, filename="foo.bar"
            )
            MockedSheetsAdaptor.sheets.add(sheet)
            MockedSheetsAdaptor(session).save_workspace(
                ["select * from s1", "select x from s1"],
                Path(fp.name),
                update_handler=update_handler
            )
            fp.seek(0)
            with zipfile.ZipFile(fp) as z:
                with z.open("info.json") as info:
                    i = json.load(info)
                with z.open("s1") as s1_csv:
                    reader = csv.reader(io.TextIOWrapper(s1_csv))
                    assert list(reader) == [["foo", "bar"]]
            assert i == {
                "queries": ["select * from s1", "select x from s1"],
                "sheets": [
                    {
                        "rows": [],
                        "name": "s1",
                        "num_rows": 1,
                        "header": ["x", "y"],
                        "filename": "foo.bar",
                    }
                ],
            }
            update_handler.on_init.assert_called_once_with(MockedSheetsAdaptor.sheets)
            update_handler.on_it.assert_called_once_with(1)

    def test_load_workspace(self, engine_factory, MockedSheetsAdaptor, update_handler):
        session = engine_factory()

        with session, tempfile.NamedTemporaryFile(mode="wb+") as fp:
            with zipfile.ZipFile(fp, mode="w") as z:
                z.writestr("s1", "foo,bar")
                z.writestr(
                    "info.json",
                    json.dumps(
                        {
                            "queries": ["select * from s1", "select x from s1"],
                            "sheets": [
                                {
                                    "rows": [],
                                    "name": "s1",
                                    "num_rows": 1,
                                    "header": ["x", "y"],
                                    "filename": "foo.bar",
                                }
                            ],
                        }
                    ),
                )
            fp.seek(0)
            ret = MockedSheetsAdaptor(session).load_workspace(
                Path(fp.name), update_handler=update_handler
            )
            assert len(MockedSheetsAdaptor.sheets) == 1
            sheet = next(iter(MockedSheetsAdaptor.sheets))
            assert sheet.name == "s1"
            assert sheet.rows == []
            assert sheet.header == ["x", "y"]
            assert sheet.filename == "foo.bar"

            rows = tuple(session.execute("select * from s1"))
            assert rows == (("foo", "bar"),)

            update_handler.on_init.assert_called_once_with(MockedSheetsAdaptor.sheets)
            update_handler.on_it.assert_called_once_with(499)
            assert ret == ["select * from s1", "select x from s1"]
