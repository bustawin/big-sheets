from __future__ import annotations

import typing as t
from dataclasses import dataclass
from pathlib import Path


class Command:
    pass


@dataclass
class AskUserForASheetOrWorkspace(Command):
    pass


@dataclass
class OpenSheet(Command):
    filepath: Path


@dataclass
class OpenWindow(Command):
    pass


@dataclass
class RemoveSheet(Command):
    name: str


@dataclass
class ExportView(Command):
    query: str
    filepath: Path


@dataclass
class SaveWorkspace(Command):
    queries: t.Collection[str, ...]
    filepath: Path


@dataclass
class LoadWorkspace(Command):
    filepath: Path
