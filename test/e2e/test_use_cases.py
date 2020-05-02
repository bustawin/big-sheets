from time import sleep
from unittest import mock

from bigsheets.adapters.ui.gui.gui import GUIAdapter
from bigsheets.app import BigSheets
from test.conftest import FIXTURES


def test_open_csv(gui, engine_factory):
    """Feature: Open CSV
      As an user, I want to open a CSV so I can see its contents.

      Scenario: Open CSV after opening the app
        Given The app opens
        And The app shows a file selector
        When I select a sheet to open
        Then I see a progress bar while the sheet is opening
        And I see some rows while the sheet is loading
        And I see the final sheet once it is opened
    """
    MockedGUIAdapter, native_window = gui
    native_window.create_file_dialog = mock.MagicMock(
        return_value=[FIXTURES / "cities.csv"]
    )
    bs = BigSheets(UI=MockedGUIAdapter, engine_factory=engine_factory)
    bs.start()
    bs.ui: GUIAdapter
    assert bs.ui.windows[0].native_window
    sleep(0.5)
    calls = MockedGUIAdapter.ctrl.mock_calls
    # Check the native window was instantiated and asked for a file dialog
    native_window.create_file_dialog.assert_called_once()
    # Check it started processing
    assert calls[4] == mock.call.Progress().start_processing(128)
    assert calls[5] == mock.call.Info().set("Opening...")
    assert calls[6][0] == "Table().set"
    assert len(calls[6].args[0]) == 49
    assert calls[6].args[1] == [
        "cities",
        "LatM",
        "LatS",
        "NS",
        "LonD",
        "LonM",
        "LonS",
        "EW",
        "City",
        "State",
    ]
    assert calls[7] == mock.call.Query().init(
        "sheet1",
        [
            "cities",
            "LatM",
            "LatS",
            "NS",
            "LonD",
            "LonM",
            "LonS",
            "EW",
            "City",
            "State",
        ],
    )
    assert calls[10] == mock.call.Progress().finish()
    # todo why not table?
    assert calls[11] == mock.call.Info().unset()
