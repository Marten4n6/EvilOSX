# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import random
import string
from abc import ABCMeta, abstractmethod

MESSAGE_INPUT = "[\033[1m?\033[0m] "
MESSAGE_INFO = "[\033[94mI\033[0m] "
MESSAGE_ATTENTION = "[\033[91m!\033[0m] "


def random_string(size=random.randint(6, 15), numbers=False):
    """:return A randomly generated string of x characters.

    :type size: int
    :type numbers: bool
    :rtype: str
    """
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


class LoaderABC:
    """Abstract base class for loaders."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_info(self):
        """:return: A dictionary containing basic information about this loader.

        :rtype: dict
        """
        pass

    def get_option_messages(self):
        """:return A list of input messages.

        :rtype: list[str]
        """
        pass

    def get_options(self, set_options):
        """The returned dictionary must contain a "loader_name" key which contains the name of this loader.

        :type
        :rtype: dict
        :return: A dictionary containing set configuration options.
        """
        pass
