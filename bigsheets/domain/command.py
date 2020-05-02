from dataclasses import dataclass
from pathlib import Path


class Command:
    pass


@dataclass
class AskUserForASheet(Command):
    pass


@dataclass
class OpenSheet(Command):
    filepath: Path

