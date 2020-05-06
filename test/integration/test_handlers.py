from unittest import mock
from unittest.mock import MagicMock

from bigsheets.domain import command, event
from bigsheets.service.command_handlers import OpenSheet
from bigsheets.service.unit_of_work import UnitOfWork
from test.conftest import FIXTURES


def test_open_sheet(engine_factory, MockedSheetsAdaptor):
    bus = MagicMock()
    uow = UnitOfWork(sheet_engine_factory=engine_factory, bus=bus,
                     Sheets=MockedSheetsAdaptor)
    os = OpenSheet(uow, MagicMock())
    cmd = command.OpenSheet(FIXTURES / "cities.csv")
    sheet = os(cmd)
    # todo check other calls
    assert bus.mock_calls[0] == mock.call.handle(
        event.SheetOpened(sheet, tuple(MockedSheetsAdaptor.sheets)))

    with uow.instantiate() as uowi:  # Check persistance
        x = uowi.session.execute("SELECT * FROM sheet1 LIMIT 1")
        assert next(x) == (41, 5, 59, "N", 80, 39, 0, "W", "Youngstown", "OH")
