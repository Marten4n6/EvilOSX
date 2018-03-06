"""Handles loading loaders."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import imp
import os
import fnmatch


class LoaderFactory:
    def __init__(self):
        self._loaders = {
            "helpers": imp.load_source("helpers", os.path.join(os.path.dirname(__file__), "loaders", "helpers.py"))
        }
        self._load_loaders()

    def _load_loaders(self):
        """Loads all loaders."""
        for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), "loaders")):
            for file_name in fnmatch.filter(files, "*.py"):
                loader_name = file_name[0:-3]
                loader_path = os.path.join(root, file_name)

                if loader_name in ["__init__", "template", "helpers"]:
                    continue

                self._loaders[loader_name] = imp.load_source(loader_name, loader_path).Loader()

    def get_loaders(self):
        """:return A list of loader classes."""
        loaders = dict(self._loaders)

        loaders.pop("helpers")
        return loaders

    def get_loader(self, index):
        """:return A tuple containing the loader's name and class."""
        for i, (key, loader) in enumerate(self.get_loaders().iteritems()):
            if i == index:
                return key, loader
