import logging
from pathlib import Path
from unittest import mock

import pytest
import webview as pywebview

from bigsheets.adapters.errors import errors as error_adapter
from bigsheets.adapters.sheets.sheets import EngineFactory, SheetsAdaptor
from bigsheets.adapters.ui.gui.gui import GUIAdapter
from bigsheets.adapters.ui.gui.query import controller

DIR = Path(__file__).parent
FIXTURES = DIR / "fixtures"

engine_counts = 0  # todo make thread safe when parallelizing tests


@pytest.fixture
def engine_factory():
    global engine_counts
    engine_counts += 1
    return EngineFactory(f"file:t{engine_counts}?mode=memory&cache=shared")


@pytest.fixture(autouse=True)
def check_logs(caplog):
    """Sets the message bus logs to INFO (so we can see what commands
    / events are executed) and ensures that no error / warning log
    is issued.
    """
    caplog.set_level(logging.DEBUG, logger="bigsheets.service.message_bus")
    yield
    for record in caplog.get_records("call"):
        assert record.levelname != "ERROR", record.exc_info
        assert record.levelname != "WARNING"


@pytest.fixture
def gui():
    native_window = mock.MagicMock()

    class MockedGUIAdapter(GUIAdapter):
        webview = mock.create_autospec(pywebview)
        webview.create_window = mock.MagicMock(return_value=native_window)
        ctrl = mock.create_autospec(controller)

        def start(self, on_loaded: callable):
            super().start(on_loaded)
            on_loaded()

    return MockedGUIAdapter, native_window


@pytest.fixture
def MockedSheetsAdaptor():
    class TestSheetsAdaptor(SheetsAdaptor):
        sheets = set()  # So we don't contaminate other tests

    return TestSheetsAdaptor


@pytest.fixture
def MockedErrorsAdapter():
    # No need to mock
    return error_adapter.ErrorsAdapter
