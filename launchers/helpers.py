from abc import ABCMeta, abstractclassmethod
import random
import string


class LauncherABC(metaclass=ABCMeta):
    """Launcher abstract base class."""

    @abstractclassmethod
    def get_info(self) -> dict:
        """:return A dictionary containing information about this launcher."""
        pass

    @abstractclassmethod
    def generate(self, stager: str) -> tuple:
        """Creates the launcher which will run the stager."""
        pass


def random_string(size=None, numbers=False):
    """:return A randomly generated string of x characters.

    If no size is specified, a random number between 6 and 15 will be used.
    """
    name = ""
    if not size:
        size = random.randint(6, 15)

    for i in range(0, size):
        if not numbers:
            name += random.choice(string.ascii_letters)
        else:
            name += random.choice(string.ascii_letters + string.digits)
    return name
