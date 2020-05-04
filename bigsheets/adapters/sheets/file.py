from __future__ import annotations

import csv
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

    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.f = self.path.open()
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
            if first_row and self.headers:
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
            subprocess.check_output("wc -l {}".format(self.path), shell=True).split()[0]
        )
