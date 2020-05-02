import logging
from time import sleep
from unittest import mock

import pytest
from more_itertools import ilen

from bigsheets.domain.command import Command
from bigsheets.service.handler import Handler
from bigsheets.service.message_bus import MessageBus


@pytest.fixture
def bus():
    return MessageBus()


class FooCommand(Command):
    def __init__(self):
        self.bar = "baz"


def test_handle_message(bus):
    fake_handler = mock.create_autospec(Handler)
    cmd = FooCommand()
    bus.start(cmd, {}, {FooCommand: {fake_handler}})
    assert bus.running.wait(timeout=3)
    sleep(0.5)  # Give some time for the handler to execute
    fake_handler.assert_called_once_with(cmd)


def test_handle_with_error(bus, caplog):
    boom = Exception("Boom!")

    def error(*args, **kwargs):
        raise boom

    bus.start(FooCommand(), {}, {FooCommand: {error}})
    sleep(0.5)
    logs = [l for l in caplog.record_tuples if 'message_bus' in l[0]]
    assert len(logs) == 2
    assert logs[1][1] == logging.ERROR
    caplog.clear()
