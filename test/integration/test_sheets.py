from unittest.mock import MagicMock, Mock, call

from bigsheets.adapters.sheets.sheets import SheetsAdaptor
from bigsheets.domain import event
from test.conftest import FIXTURES


class TestSheets:
    def test_open_sheet(self, engine_factory):
        e = engine_factory()
        initial_callback: Mock = MagicMock()
        callback = MagicMock()
        sheet = SheetsAdaptor(e).open_sheet(
            FIXTURES / "cities.csv", initial_callback, callback
        )
        # Check sheet object
        assert sheet.name == "sheet1"
        assert sheet.num_rows == 128
        assert sheet.rows
        assert isinstance(sheet.events[0], event.SheetOpened)

        # Check callbacks
        # todo change with mock_calls
        initial_callback.assert_called_once_with(sheet)
        callback.assert_has_calls([call(sheet, 99), call(sheet, 198)])

        # Check db
        x = e.execute("SELECT * FROM sheet1 LIMIT 1")
        assert next(x) == (41, 5, 59, "N", 80, 39, 0, "W", "Youngstown", "OH")
