# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Perform a slowloris DoS attack.",
            "References": [
                "https://en.wikipedia.org/wiki/Slowloris_(computer_security)",
                "https://github.com/ProjectMayhem/PySlowLoris"
            ],
            "Stoppable": False
        }

    def get_setup_messages(self):
        return [
            "Target to attack (example: fbi.gov:443): "
        ]

    def setup(self, set_options):
        # This attack only works on Apache 1x, 2x, dhttpd, and some other minor servers.
        # Servers like nginx are not vulnerable to this form of attack.
        # If no port is specified 80 will be used.
        target = set_options[0]

        if not target:
            self._view.display_error("Invalid target.")
            return False, None
        else:
            return True, {
                "target": target
            }
