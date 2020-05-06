from __future__ import annotations

import csv
import io
import logging
import subprocess
import typing as t
from decimal import Decimal
from functools import cached_property
from itertools import islice
from pathlib import Path

Cell = t.Union[int, float, str, None]
Cells = Row = Column = t.Collection[Cell]
Rows = t.Collection[Row]
SQLiteTypes = t.Union[t.Type[Decimal], t.Type[str]]


class CSVFile:
    """The repository for a CSV in the form of a file."""

    SAMPLE = 50
    KB_SAMPLE = 4092

    def __init__(
        self, path: Path, headers: t.Optional[t.List[str]] = None, binary=False
    ):
        """
        :param path:
        :param headers: The headers of the CSV. If not provided,
        they are guessed from the file.
        :param binary: Whether the file the path opens is in binary
        or str mode. Unless the docs says otherwise, it is usually
        in text.
        """
        self.path = path
        self.headers: t.List[str] = headers
        self.binary = binary

    def __enter__(self):
        self.f = self.path.open()
        if self.binary:
            self.f = io.TextIOWrapper(self.f)
        sniffer = csv.Sniffer()
        line = self.f.readline()
        self.dialect = sniffer.sniff(line)
        print(vars(self.dialect))
        logging.info("File %s: dialect %s", self.path, self.dialect)
        self.f.seek(0)

        self.reader = csv.reader(self.f, self.dialect)
        self.rows = list(islice(self.reader, self.SAMPLE))
        self.f.seek(0)
        self.num_cells = len(self.rows[0])

        # Compute column info
        if not self.headers:
            if sniffer.has_header(self.f.read(self.KB_SAMPLE)):
                self.headers = self.rows.pop(0)  # Remove first row when is header
            else:
                self.headers = tuple(f"C{i}" for i in range(self.num_cells))
            self.f.seek(0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()

    def __iter__(self):
        first_row = True
        for row in iter(self.reader):
            if first_row and row == self.headers:
                # Do not return the first row if it is a header
                first_row = False
                continue
            yield row

    @property
    def name(self):
        """The name of the file."""
        return self.path.name

    @cached_property
    def num_lines(self) -> int:
        return int(
            subprocess.check_output(f"wc -l '{self.path}'", shell=True).split()[0]
        )
