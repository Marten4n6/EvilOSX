"""Boilerplate code used by launchers."""
import random
import string


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
