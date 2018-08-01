# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import ModuleABC


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Retrieve iCloud contacts.",
            "References": [
                "https://github.com/manwhoami/iCloudContacts"
            ],
            "Stoppable": False
        }
