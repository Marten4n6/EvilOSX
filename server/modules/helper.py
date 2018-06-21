# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import random
import string
from abc import ABCMeta, abstractmethod
from os import path
from typing import Tuple, Optional

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


class ModuleABC(metaclass=ABCMeta):
    """Abstract base class for modules."""

    @abstractmethod
    def get_info(self) -> dict:
        """:return: A dictionary containing basic information about this module."""
        pass

    def setup(self, view) -> Tuple[bool, Optional[dict]]:
        """Interacts with the user, used to set configuration options.

        :return: A tuple containing a "was the setup successful" boolean and configuration options (which may be None).
        """
        return True, None

    def process_response(self, response: bytes, view, response_options: dict):
        """Processes the module's response."""
        view.output_separator()
        view.output(response)
