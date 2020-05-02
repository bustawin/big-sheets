from __future__ import annotations

import asyncio
import logging
import threading
import typing as t
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from threading import Thread

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

    Although this bus handles commands, it does not return a response
    to the caller. So, this bus treats commands and events the
    same way.
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
        self.thread = Thread(
            target=self._start, name=self.__class__.__name__, daemon=True,
        )
        self.running = threading.Event()
        """Whether the message bus is ready to handle messages."""
        self._pool = ThreadPoolExecutor(
            max_workers=5, thread_name_prefix=self.__class__.__name__
        )

    def start(
        self, message: Message, event_handlers: Handlers, command_handlers: Handlers,
    ):
        """Registers handlers, starts running the event loop, and
        executes the handlers of the passed-in message.
        """
        assert threading.current_thread().name != self.__class__.__name__
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.thread.start()
        self.running.wait()
        self.handle(message)

    def handle(self, message: Message):
        """Handle a message."""
        assert threading.current_thread().name != self.__class__.__name__

        assert self.loop.is_running(), "Loop is not running"

        self.loop.call_soon_threadsafe(
            partial(asyncio.create_task, self._handle(message))
        )

    def _start(self):
        assert threading.current_thread().name == self.__class__.__name__
        self.loop = asyncio.new_event_loop()
        self.loop.call_soon(lambda: self.running.set())
        self.loop.run_forever()

    async def _handle(self, message: Message):
        """Handle a message in another thread."""
        assert threading.current_thread().name == self.__class__.__name__
        handlers = (
            self.event_handlers
            if isinstance(message, event.Event)
            else self.command_handlers
        )
        handlers_for_message = handlers.get(message.__class__)
        if not handlers_for_message:
            log.error("No handlers defined for %s", message)
            return

        for handler in handlers_for_message:
            self.loop.run_in_executor(self._pool, partial(self._exec, handler, message))

    def _exec(self, handler, message):
        name = threading.current_thread().name
        log.debug("Executing %s with %s on %s", message, handler, name)
        try:
            handler(message)
        except running.Exiting:
            log.debug("Exiting exception from %s with %s on %s", message, handler, name)
        except Exception:
            log.exception("Exception from %s with %s on %s", message, handler, name)
        else:
            log.debug("Finished execution of %s with %s on %s.", message, handler, name)
