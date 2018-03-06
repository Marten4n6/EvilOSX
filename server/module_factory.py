"""Handles loading modules."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import imp
import os
import fnmatch


class ModuleFactory:
    def __init__(self):
        self._modules = {}
        self._load_modules()

    def _load_modules(self):
        """Loads all modules."""
        for root, dirs, files in os.walk("modules"):
            for file_name in fnmatch.filter(files, "*.py"):
                module_name = file_name[0:-3]
                module_path = os.path.join(root, file_name)

                if module_name in ["__init__", "template", "helpers"]:
                    continue

                self._modules[module_name] = imp.load_source(module_name, module_path).Module()

    def get_modules(self):
        """:return A list of module classes."""
        return self._modules

    def get_module(self, module_name):
        """:return The class of the specified module name.

        :type module_name str
        """
        return self._modules[module_name]
