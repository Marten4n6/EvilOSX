# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import random
import string
from abc import ABCMeta, abstractmethod
from os import path
from typing import Tuple, List, Optional

DATA_DIRECTORY = path.realpath(path.join(path.dirname(__file__), path.pardir, path.pardir, "data"))
OUTPUT_DIRECTORY = path.join(DATA_DIRECTORY, "output")


def random_string(size: int = random.randint(6, 15), numbers: bool = False) -> str:
    """:return A randomly generated string of x characters."""
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


class ModuleViewABC(metaclass=ABCMeta):
    """Abstract base class which allows modules to interact with the view."""

    @abstractmethod
    def display_error(self, text: str):
        """Displays an error message to the user."""
        pass

    @abstractmethod
    def display_info(self, text: str):
        """Displays an information message to the user."""
        pass

    @abstractmethod
    def should_continue(self, messages: List[str]) -> bool:
        """Shows the list of messages and asks the user if they want to continue."""
        pass

    @abstractmethod
    def output(self, line: str, prefix=""):
        """Outputs a message to the response view."""
        pass

    def output_separator(self):
        self.output("-" * 5)


class ModuleABC(metaclass=ABCMeta):
    """Abstract base class for modules."""

    def __init__(self, view: ModuleViewABC, model):
        self._view = view
        self._model = model

    @abstractmethod
    def get_info(self) -> dict:
        """:return: A dictionary containing basic information about this module."""
        pass

    def get_setup_messages(self) -> List[str]:
        """:return A list of input messages."""
        return []

    def setup(self, set_options: list) -> Tuple[bool, Optional[dict]]:
        """:return: A tuple containing a "was the setup successful" boolean and configuration options."""
        return True, None

    def process_response(self, response: bytes, response_options: dict):
        """Processes the module's response."""
        self._view.output(response.decode())
