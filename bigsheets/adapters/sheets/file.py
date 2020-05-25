from __future__ import annotations

import csv
import io
import logging
import subprocess
import typing as t
from decimal import Decimal
from functools import cached_property
from itertools import islice

Cell = t.Union[int, float, str, None]
Cells = Row = Column = t.Collection[Cell]
Rows = t.Collection[Row]
SQLiteTypes = t.Union[t.Type[Decimal], t.Type[str]]


class CSVFile:
    """The repository for a CSV in the form of a file."""
    # This method used to work with a path not a file directly
    # however we could not use it with zip files because
    # of https://bugs.python.org/issue40564

    SAMPLE = 50
    KB_SAMPLE = 4092

    def __init__(
        self, f: t.TextIO, headers: t.Optional[t.List[str]] = None
    ):
        """
        :param f: The CSV file.
        :param headers: The headers of the CSV. If not provided,
        they are guessed from the file.
        :param binary: Whether the file the path opens is in binary
        or str mode. Unless the docs says otherwise, it is usually
        in text.
        """
        self.f = f
        self.headers: t.List[str] = headers
        sniffer = csv.Sniffer()
        line = self.f.readline()
        self.dialect = sniffer.sniff(line)
        logging.info("File %s: dialect %s", self.name, vars(self.dialect))
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
        return self.f.name

    @cached_property
    def num_lines(self) -> int:
        return int(
            subprocess.check_output(f"wc -l '{self.name}'", shell=True).split()[0]
        )
