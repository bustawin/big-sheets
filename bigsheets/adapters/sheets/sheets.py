import abc
import logging
import sqlite3
from pathlib import Path

import more_itertools

from bigsheets.adapters.sheets.file import CSVFile
from bigsheets.domain import model
from bigsheets.service import running


class EngineFactory:
    """Returns the db engine upon call."""

    def __init__(self, uri="file:db?mode=memory&cache=shared"):
        self.uri = uri
        self._keep_alive = None
        """Keeps the database alive by keeping a live connection to it."""

    def __call__(self) -> sqlite3.Connection:
        if not self._keep_alive:
            self._keep_alive = self._connect(self.uri)
        return self._connect(self.uri)

    @staticmethod
    def _connect(uri):
        return sqlite3.connect(uri, uri=True)


engine_factory = EngineFactory()


class SheetsPort(abc.ABC):
    """The repository of sheets as part of the infrastructure layer.

    This class loads, queries, and saves sheets.
    """

    def __init__(self, session):
        self.session = session

    @abc.abstractmethod
    def open_sheet(
        self, filepath: Path, initial_callback: callable, callback: callable,
    ) -> model.Sheet:
        raise NotImplementedError

    @abc.abstractmethod
    def number_of_sheets(self) -> int:
        raise NotImplementedError


class SheetsAdaptor(SheetsPort):
    """The repository of sheets."""

    SQLITE_VAR_LIMIT = 999
    """Max number of variables in queries for sqlite."""

    session: sqlite3.Connection

    def open_sheet(
        self, filepath: Path, initial_callback: callable, callback: callable,
    ) -> model.Sheet:
        with CSVFile(filepath) as file:
            table_name = model.new_sheet_name(self.number_of_sheets())
            sheet = model.Sheet(
                table_name, rows=file.rows, header=file.headers, num_rows=file.num_lines
            )
            initial_callback(sheet)
            sheet.wrongs = []
            num_opened = 0
            for wrongs in self._process_spreadsheet(file, table_name):
                running.exit_if_asked()
                sheet.wrongs.extend(wrongs)
                num_opened += self.rows_per_chunk(file.num_cells)
                callback(sheet, num_opened)
        sheet.opened()
        return sheet

    def number_of_sheets(self) -> int:
        return more_itertools.ilen(
            self.session.execute("SELECT name FROM sqlite_master WHERE type='table'")
        )

    def _create_table_q(self, table_name, headers: model.Row):
        cols = (f"{name} NUMERIC" for name in headers)
        return f"CREATE TABLE {table_name} ({','.join(cols)})"

    def _process_spreadsheet(self, f: CSVFile, table_name):
        # create table
        self.session.execute(self._create_table_q(table_name, f.headers))

        # Insert in chunks
        for rows in more_itertools.ichunked(f, self.rows_per_chunk(f.num_cells)):
            wrongs, goods = more_itertools.partition(
                lambda r: len(r) == f.num_cells, rows
            )
            goods = list(goods)

            # Insert
            values = (f"({','.join('?' for _ in row)})" for row in goods)
            q = f"INSERT INTO {table_name} VALUES {','.join(values)};"
            try:
                self.session.execute(q, list(more_itertools.flatten(goods)))
            except Exception as e:
                logging.error("Exception in rows %s", goods)
                raise e
            yield wrongs

    def rows_per_chunk(self, cols: int):
        return self.SQLITE_VAR_LIMIT // cols
