# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import random
import string
from abc import ABCMeta, abstractmethod
from os import path

from server.model import Model

DATA_DIRECTORY = path.realpath(path.join(path.dirname(__file__), path.pardir, path.pardir, "data"))
OUTPUT_DIRECTORY = path.join(DATA_DIRECTORY, "output")


def random_string(size=random.randint(6, 15), numbers=False):
    """
    :type size: int
    :type numbers: bool
    :rtype: str
    :return A randomly generated string of x characters.
    """
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


class ModuleViewABC:
    """Abstract base class which allows modules to interact with the view."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def display_error(self, text):
        """Displays an error message to the user.

        :type text: str
        """
        pass

    @abstractmethod
    def display_info(self, text):
        """Displays an information message to the user.

        :type text: str
        """
        pass

    @abstractmethod
    def should_continue(self, messages):
        """Shows the list of messages and asks the user if they want to continue.

        :type messages: list[str]
        :rtype: bool
        """
        pass

    @abstractmethod
    def output(self, line, prefix=""):
        """Outputs a message to the response view.

        :type line: str
        :type prefix: str
        """
        pass

    def output_separator(self):
        self.output("-" * 5)


class ModuleABC:
    """Abstract base class for modules."""
    __metaclass__ = ABCMeta

    def __init__(self, view, model):
        """
        :type view: ModuleViewABC
        :type model: Model
        """
        self._view = view
        self._model = model

    @abstractmethod
    def get_info(self):
        """
        :rtype: dict
        :return: A dictionary containing basic information about this module.
        """
        pass

    def get_setup_messages(self):
        """
        :rtype: list[str]
        :return A list of input messages.
        """
        return []

    def setup(self, set_options):
        """:return: A tuple containing a "was the setup successful" boolean and configuration options.

        :type set_options: list
        :rtype: tuple[bool, dict or None]
        """
        return True, None

    def process_response(self, response, response_options):
        """Processes the module's response.

        :type response: bytes
        :type response_options: dict
        """
        self._view.output_separator()
        self._view.output(response.decode())
