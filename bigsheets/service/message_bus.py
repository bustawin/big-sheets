from __future__ import annotations

import logging
import threading
import typing as t
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial, singledispatchmethod

from bigsheets.domain import command, event
from bigsheets.service import handler as h, running

log = logging.getLogger(__name__)

Message = t.Union[command.Command, event.Event]
MessageType = t.Union[t.Type[command.Command], t.Type[event.Event]]
Handlers = t.Dict[MessageType, t.Set[h.Handler]]


class MessageBus:
    """A message bus using the message broker pattern for an event
    driven system.

    Receives messages (events and commands) and executes them through
    previously registered handlers.

    Events are sent to multiple event handlers (listeners)
    asynchronously, and each handler fails independently.

    Commands are sent to one command handler (listener) synchronously,
    so the caller blocks and gets the result of the handler, as when
    executing a regular function.

    +----------------+--------------------+-----------------+
    |                | Event              | Command         |
    +----------------+--------------------+-----------------+
    | Named          | Past tense         | Imperative mood |
    +----------------+--------------------+-----------------+
    | Error handling | Fail independently | Fail noisily    |
    +----------------+--------------------+-----------------+
    | Sent to        | All listeners      | One recipient   |
    +----------------+--------------------+-----------------+
    """

    # This implementation internally uses the asyncio loop as the event
    # loop in an isolated thread (which is called "AsyncMessageBus"),
    # and executes handlers in a thread execution pool —both senders
    # and handlers are regular blocking functions executed in other threads.

    def __init__(self):
        event_handlers: Handlers
        command_handlers: Handlers
        # Although ideally the handlers should be imported in creation
        # time, this creates a circular dependency
        """Whether the message bus is ready to handle messages."""
        self._pool = ThreadPoolExecutor(
            max_workers=5, thread_name_prefix=self.__class__.__name__
        )

    def start(
        self, event_handlers: Handlers, command_handlers: Handlers,
    ):
        """Registers handlers, starts running the event loop, and
        executes the handlers of the passed-in message.
        """
        # todo we should init event / commands in __init__  now now
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    @singledispatchmethod
    def handle(self, message):
        """Handle a message."""
        raise TypeError(f"{message} is not a command or event.")

    @handle.register
    def _(self, command: command.Command):
        handlers = self._get_handlers(command, self.command_handlers)
        assert len(handlers) == 1, "Commands can only have one handler"
        return self._exec(next(iter(handlers)), command)

    @handle.register
    def _(self, event: event.Event):
        """Handle a message in another thread."""
        for handler in self._get_handlers(event, self.event_handlers):
            self._pool.submit(partial(self._exec, handler, event))

    def _exec(self, handler, message):
        name = threading.current_thread().name
        log.debug("Executing %s with %s on %s", message, handler, name)
        try:
            r = handler(message)
        except running.Exiting:
            log.debug("Exiting exception from %s with %s on %s", message, handler, name)
            raise
        except Exception:
            log.exception("Exception from %s with %s on %s", message, handler, name)
            raise
        else:
            log.debug(
                "Finished execution of %s with %s on %s with result %s",
                message,
                handler,
                name,
                r,
            )
            return r

    def _get_handlers(self, message: Message, handlers: Handlers):
        message_handlers = handlers.get(message.__class__)
        if not message_handlers:
            raise NoHandlersDefined(message)
        return message_handlers


class NoHandlersDefined(Exception):
    def __init__(self, message: Message):
        self.message = message
