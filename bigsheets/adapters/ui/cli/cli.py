import abc
from dataclasses import dataclass


class CLIPort(abc.ABC):
    """The primary adaptor for the Command Line (user) Interface
     using the Presenter pattern.
     """
    # todo ensure presenter pattern


@dataclass
class CLIAdapter(CLIPort):
    window = WindowManager
    ctrl = Controller
    view = View
