from abc import ABCMeta, abstractclassmethod
import random
import string

MESSAGE_INPUT = "\033[1m" + "[?] " + "\033[0m"
MESSAGE_INFO = "\033[94m" + "[I] " + "\033[0m"
MESSAGE_ATTENTION = "\033[91m" + "[!] " + "\033[0m"


class LoaderABC(metaclass=ABCMeta):
    """Abstract base class for loaders."""

    @abstractclassmethod
    def get_info(self) -> dict:
        """:return A dictionary containing information about this loader."""
        pass

    @abstractclassmethod
    def setup(self) -> dict:
        """:return A dictionary containing configuration options (with the launcher name as the key)."""
        pass

    @abstractclassmethod
    def generate(self, loader_options: dict, payload_options: dict, payload: str) -> str:
        """Generates the loader which decides how the payload will be loaded by the stager."""
        pass

    @abstractclassmethod
    def remove_payload(self) -> str:
        """Removes the payload."""
        pass

    @abstractclassmethod
    def update_payload(self, server_host: str, server_port: int) -> str:
        """Updates the payload to a new server host/port."""
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
