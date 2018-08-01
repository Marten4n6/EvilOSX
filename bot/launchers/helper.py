# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import random
import string
from abc import ABCMeta, abstractmethod


def random_string(size=random.randint(6, 15), numbers=False):
    """
    :type size: int
    :type numbers: bool
    :rtype: str
    :return A randomly generated string of x characters."""
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


class LauncherABC:
    """Abstract base class for launchers."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def generate(self, stager):
        """
        :type stager: str
        :rtype: (str, str)
        :return A tuple containing the file extension and code of the launcher.
        """
        pass
