from __future__ import annotations

import abc
import typing as t
from collections import defaultdict

from ordered_set_37 import OrderedSet

from bigsheets.domain import error as model


class Errors(abc.ABC):
    """The repository of errors as part of the infrastructure layer.

    This class gets and saves errors.
    """
    def get(self) -> t.Dict[str, OrderedSet[model.Error]]:
        raise NotImplementedError

    def add(self, *error: model.Error):
        raise NotImplementedError


class ErrorsAdapter(Errors):
    def __init__(self):
        self._errors: t.Dict[str, OrderedSet[model.Error]] = defaultdict(
            OrderedSet
        )

    def get(self):
        return self._errors

    def add(self, *error: model.Error):
        for e in error:
            self._errors[e.filename].add(e)
