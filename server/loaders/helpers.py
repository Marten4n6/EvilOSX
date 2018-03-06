"""Boilerplate code used by the loader's setup method."""
import random
import string

MESSAGE_INPUT = "\033[1m" + "[?] " + "\033[0m"
MESSAGE_INFO = "\033[94m" + "[I] " + "\033[0m"
MESSAGE_ATTENTION = "\033[91m" + "[!] " + "\033[0m"


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
