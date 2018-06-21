# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import random
import string
from abc import ABCMeta, abstractmethod


def random_string(size: int = random.randint(6, 15), numbers: bool = False) -> str:
    """:return A randomly generated string of x characters."""
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


class LauncherABC(metaclass=ABCMeta):
    """Abstract base class for launchers."""

    @abstractmethod
    def generate(self, stager: str) -> tuple:
        """:return A tuple containing the file extension and code of the launcher."""
        pass
