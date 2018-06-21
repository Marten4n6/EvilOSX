# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from abc import ABCMeta, abstractmethod
import random
import string

MESSAGE_INPUT = "[\033[1m?\033[0m] "
MESSAGE_INFO = "[\033[94mI\033[0m] "
MESSAGE_ATTENTION = "[\033[91m!\033[0m] "


def random_string(size: int = random.randint(6, 15), numbers: bool = False) -> str:
    """:return A randomly generated string of x characters."""
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


class LoaderABC(metaclass=ABCMeta):
    """Abstract base class for loaders."""

    @abstractmethod
    def get_info(self) -> dict:
        """:return: A dictionary containing basic information about this loader."""
        pass

    def setup(self) -> dict:
        """This method is called by the builder.

        The returned dictionary must contain a "loader_name" key which contains the name of this loader.
        :return: A dictionary containing configuration options.
        """
        pass
