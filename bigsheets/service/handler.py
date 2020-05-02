from __future__ import annotations

import abc
import typing as t

from bigsheets.domain import command, event

Message = t.Union[event.Event, command.Command]


class Handler(abc.ABC):
    HANDLES: t.Set[t.Union[t.Type[event.Event], t.Type[command.Command]]]

    @abc.abstractmethod
    def __call__(self, message: Message):
        raise NotImplementedError

    def __hash__(self):
        # We assume instances are singletons
        return hash(self.__class__.__name__)

    def __repr__(self):
        return f"<Handler {self.__class__.__name__}>"


Handlers = t.Set[t.Type[Handler]]
