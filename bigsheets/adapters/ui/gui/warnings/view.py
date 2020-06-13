from __future__ import annotations

from dataclasses import dataclass

from bigsheets.adapters.ui.gui import utils as gui_utils
from bigsheets.service import read_model


# noinspection PyUnresolvedReferences


@dataclass
class View:
    reader: read_model.ReadModel

    @gui_utils.log_exception
    def errors(self):
        return {
            k: [e.dict() for e in errors]
            for k, errors in self.reader.errors().items()
        }
