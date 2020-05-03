import logging
from time import sleep
from unittest import mock

import pytest

from bigsheets.domain.command import Command
from bigsheets.domain.event import Event
from bigsheets.service.handler import Handler
from bigsheets.service.message_bus import MessageBus


@pytest.fixture
def bus():
    return MessageBus()


class FooCommand(Command):
    def __init__(self):
        self.bar = "baz"


class FooEvent(Event):
    def __init__(self):
        self.bar = "baz"


def test_handle_command(bus):
    fake_handler = mock.create_autospec(Handler)
    fake_handler.return_value = "returned!"
    cmd = FooCommand()
    bus.start({}, {FooCommand: {fake_handler}})
    result = bus.handle(cmd)
    fake_handler.assert_called_once_with(cmd)
    assert result == "returned!"


def test_handle_command_with_error(bus, caplog):
    boom = Exception("Boom!")

    def error(*args, **kwargs):
        raise boom

    bus.start({}, {FooCommand: {error}})
    with pytest.raises(Exception, match="Boom!"):
        bus.handle(FooCommand())
    logs = [l for l in caplog.record_tuples if "message_bus" in l[0]]
    assert len(logs) == 2
    assert logs[1][1] == logging.ERROR
    caplog.clear()


def test_handle_event(bus):
    fake_handler = mock.create_autospec(Handler)
    event = FooEvent()
    bus.start({FooEvent: {fake_handler}}, {})
    bus.handle(event)
    sleep(0.5)  # Give some time for the handler to execute
    fake_handler.assert_called_once_with(event)


def test_handle_event_with_error(bus, caplog):
    boom = Exception("Boom!")

    def error(*args, **kwargs):
        raise boom

    event = FooEvent()
    bus.start({FooEvent: {error}}, {})
    bus.handle(event)
    sleep(0.5)
    logs = [l for l in caplog.record_tuples if "message_bus" in l[0]]
    assert len(logs) == 2
    assert logs[1][1] == logging.ERROR
    caplog.clear()
