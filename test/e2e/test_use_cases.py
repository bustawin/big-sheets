from time import sleep
from unittest import mock

import pytest

from bigsheets.adapters.ui.gui.gui import GUIAdapter
from bigsheets.app import BigSheets
from test.conftest import FIXTURES


def test_open_csv_sheet_when_opening_the_app(gui, engine_factory):
    """Feature: Open a CSV sheet when opening the app
      As an user, I want to open a CSV so I can see its contents.

      Scenario: Open a CSV sheet when opening the app
        Given The app opens
        Then the app shows a file selector

      Scenario: User selects the CSV sheet file to open


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
    assert calls[6] == mock.call.Progress().start_processing(128)
    assert calls[7] == mock.call.Info().set(
        "Some functionality is disabled until the sheet finishes opening."
    )
    assert calls[8][0] == "Table().set"
    assert len(calls[8].args[0]) == 49
    assert calls[8].args[1] == [
        "cities",
        "LatM",
        "LatS",
        "NS",
        "Lon D",
        "Lon M",
        "LonS",
        "EW",
        "City",
        "State",
    ]
    assert calls[9] == mock.call.Query().init("sheet1")
    assert calls[13] == mock.call.Progress().finish()
    # todo why not table?
    assert calls[14] == mock.call.Info().unset()


@pytest.mark.skip(reason="Test not developed.")
def test_open_another_sheet_once_the_app_is_opened():
    """Feature: Open another CSV sheet once the app is opened
    As an user, I want to open more sheets once I have an initial
    sheet opened.

    Scenario: User opens the file selector
      Given An opened app
      When I click on an "Open Sheet" button
      Then The app shows a file selector

    Scenario: User selects the CSV sheet file to open
      Given I opened the file selector
      When I select the CSV sheet and click open
      Then The app adds the newly opened sheet into a window

    Scenario: App opens the CSV shee




    Opens another sheet with a new window,
    and added into the sheet list.
    """


class TestQuery:
    """Feature: Query the sheet
    As an user, I want to write and submit queries so I can see what
    I want in the sheet.
    """

    def test_query_the_sheet(self, gui, engine_factory):
        """Scenario: Query the sheet

        Given A sheet is opened
        When I type a query and submit it
        Then I see the resulting sheet of applying the query
        """
        MockedGUIAdapter, native_window = gui
        native_window.create_file_dialog = mock.MagicMock(
            # Create a sheet1 with cities.csv content
            return_value=[FIXTURES / "cities.csv"]
        )
        bs = BigSheets(UI=MockedGUIAdapter, engine_factory=engine_factory)
        bs.start()
        bs.ui: GUIAdapter

        bs.ui.windows[-1]._view.query("select * from sheet1", 1, 0)
        # We get the first row of the csv
        # Note that mock_calls[0] is the temp table created when loading
        # the csv (which we assert in test_open_csv)
        assert bs.ui.windows[-1].ctrl.table.set.mock_calls[1] == mock.call(
            ((41, 5, 59, "N", 80, 39, 0, "W", "Youngstown", "OH"),),
            (
                "cities",
                "LatM",
                "LatS",
                "NS",
                "Lon D",
                "Lon M",
                "LonS",
                "EW",
                "City",
                "State",
            ),
        )

    @pytest.mark.skip(reason="Test not developed.")
    def test_wrong_query(self):
        """Scenario: User wrote the query wrongly.

        Given A sheet is opened
        When I wrongly type a query and submit it
        Then I see an error message hinting where the error is.
        """


@pytest.mark.skip(reason="Test not developed.")
def test_export_view():
    # integration / test_sheets has a non-e2e test_export_view
    pass


@pytest.mark.skip(reason="Test not developed.")
def test_save_workspace():
    pass


@pytest.mark.skip(reason="Test not developed.")
def test_load_workspace():
    pass


@pytest.mark.skip(reason="Test not developed.")
def test_close_sheet():
    pass


@pytest.mark.skip(reason="Test not developed.")
def test_close_window():
    pass


@pytest.mark.skip(reason="Test not developed.")
def test_close_app():
    pass
