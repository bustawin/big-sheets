from __future__ import annotations

import abc
import csv
import io
import json
import logging
import sqlite3
import typing as t
import zipfile
from itertools import chain
from pathlib import Path

import more_itertools
import zipstream

from bigsheets.adapters.sheets.file import CSVFile
from bigsheets.domain import error as error_model, sheet as sheet_model
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


class UpdateHandler:
    """Receives updates from SheetsPort methods that take time to complete.

    Override this class to implement handlers for such updates. Some
    methods from SheetsPort accept an instance of this class as an argument.
    """
    # Idea from https://softwareengineering.stackexchange.com/a/409941

    def __init__(self):
        self.total = 0

    def on_init(self, sheet: t.Union[sheet_model.Sheet, t.Collection[sheet_model.Sheet]]):
        pass

    def on_it(self, n: int):
        self.total += n


class Sheets(abc.ABC):
    """The repository of sheets as part of the infrastructure layer.

    This class loads, queries, and saves sheets.
    """

    def __init__(self, session):
        self.session = session

    @abc.abstractmethod
    def open_sheet(
        self, filepath: Path, update_handler: UpdateHandler = UpdateHandler(),
    ) -> t.Tuple[sheet_model.Sheet, t.List[error_model.WrongRow]]:
        raise NotImplementedError

    @abc.abstractmethod
    def number_of_sheets(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def remove_sheet(self, *, name: str) -> sheet_model.Sheet:
        """Removes a sheet (ie. closes)."""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self) -> t.Iterator[sheet_model.Sheet]:
        """Gets all the sheets."""
        raise NotImplementedError

    @abc.abstractmethod
    def export_view(self, query: str, filepath: Path):
        """Saves the result of executing query in filepath as a CSV."""
        raise NotImplementedError

    @abc.abstractmethod
    def save_workspace(
        self,
        queries: t.Collection[str],
        filepath: Path,
        update_handler: UpdateHandler = UpdateHandler(),
    ):
        """Saves the queries, sheets, and rows into a bigsheets file."""
        raise NotImplementedError

    @abc.abstractmethod
    def load_workspace(
        self, filepath: Path, update_handler: UpdateHandler = UpdateHandler()
    ) -> t.List[str]:
        """Loads the queries, sheets, and rows from a bigsheets file
        created by "save_workspace".
        """
        raise NotImplementedError


class SheetsAdaptor(Sheets):
    """The repository of sheets."""

    SQLITE_VAR_LIMIT = 999
    """Max number of variables in queries for sqlite."""

    sheets: t.Set[sheet_model.Sheet] = set()
    """The opened sheets models."""
    # todo use a thread-safe structure and testing
    #   And probably this could be taken into its own class

    session: sqlite3.Connection

    def open_sheet(
        self, filepath: Path, update_handler: UpdateHandler = UpdateHandler()
    ) -> t.Tuple[sheet_model.Sheet, t.List[error_model.WrongRow]]:
        with filepath.open() as f:
            file = CSVFile(f)
            table_name = sheet_model.new_sheet_name(self.number_of_sheets())
            sheet = sheet_model.Sheet(
                table_name,
                rows=file.rows,
                header=file.headers,
                num_rows=file.num_lines,
                filename=file.name,
            )
            self.sheets.add(sheet)
            update_handler.on_init(sheet)
            wrong_rows = []
            for wrongs in self._process_spreadsheet(file, table_name):
                running.exit_if_asked()
                wrong_rows.extend(
                    error_model.WrongRow(sheet.filename, sheet.name, wrong)
                    for wrong in wrongs
                )
                new_rows = self.rows_per_chunk(file.num_cells)
                update_handler.on_it(new_rows)
        return sheet, wrong_rows

    def number_of_sheets(self) -> int:
        return more_itertools.ilen(
            self.session.execute("SELECT name FROM sqlite_master WHERE type='table'")
        )

    def _create_table_q(self, table_name, headers: sheet_model.Row):
        cols = (f"'{name}' NUMERIC" for name in headers)
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
        """The maximum number of rows that can be processed per chunk."""
        # Note that the last chunk might have lesser rows
        return self.SQLITE_VAR_LIMIT // cols

    def remove_sheet(self, *, name: str) -> sheet_model.Sheet:
        sheet = next(sheet for sheet in self.sheets if sheet.name == name)
        self.session.execute(f"DROP TABLE {name}")
        self.sheets.remove(sheet)
        sheet.remove(self.sheets)
        return sheet

    def get(self):
        return iter(self.sheets)

    def query(self, query: str):
        cursor: sqlite3.Cursor = self.session.execute(query)
        headers = tuple(h[0] for h in cursor.description)
        return headers, cursor

    def export_view(self, query: str, filepath: Path):
        headers, rows = self.query(query)
        with filepath.open(mode="w") as f:
            writer = csv.writer(f)
            writer.writerows(chain([headers], rows))

    def save_workspace(
        self,
        queries: t.Collection[str],
        filepath: Path,
        update_handler: UpdateHandler = UpdateHandler(),
    ):
        zip = zipstream.ZipFile(allowZip64=True, compression=zipfile.ZIP_DEFLATED)
        # Save sheets
        update_handler.on_init(self.sheets)
        for sheet in self.sheets:
            _, rows = self.query(f"SELECT * FROM {sheet.name}")
            writer = csv.writer(FileLike())

            zip.write_iter(sheet.name, self._csv_gen(rows, writer, update_handler))

        info = {
            "queries": tuple(queries),
            "sheets": [self._export_sheet(sheet) for sheet in self.sheets],
        }
        zip.writestr("info.json", json.dumps(info).encode())
        with filepath.open("wb") as file:
            for data in zip:
                file.write(data)

    def _csv_gen(self, rows, writer, update_handler):
        for row in rows:
            yield writer.writerow(row).encode()
            update_handler.on_it(1)

    def load_workspace(self, filepath: Path, update_handler=UpdateHandler()):
        with zipfile.ZipFile(filepath) as file:
            with file.open("info.json") as info:
                i = json.load(info)
                self.sheets.clear()
                for s in i["sheets"]:
                    sheet = sheet_model.Sheet(
                        name=s["name"],
                        rows=s["rows"],
                        header=s["header"],
                        num_rows=s["num_rows"],
                        filename=s["filename"],
                    )
                    self.sheets.add(sheet)
                update_handler.on_init(self.sheets)
            for sheet in self.sheets:
                with file.open(sheet.name) as inner:
                    csv_sheets = CSVFile(io.TextIOWrapper(inner), headers=sheet.header)
                    for _ in self._process_spreadsheet(csv_sheets, sheet.name):
                        rows_opened = self.rows_per_chunk(csv_sheets.num_cells)
                        update_handler.on_it(rows_opened)
        return i["queries"]

    def _export_sheet(self, sheet: sheet_model.Sheet):
        # We cannot use pydantic because
        # https://github.com/pyinstaller/pyinstaller/issues/4406
        return {
            "rows": sheet.rows,
            "name": sheet.name,
            "num_rows": sheet.num_rows,
            "header": sheet.header,
            "filename": sheet.filename,
        }


class FileLike:
    def write(self, row: str):
        return row
