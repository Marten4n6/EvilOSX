# -*- coding: utf-8 -*-
"""Creates loaders using the factory pattern."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

from os import path, listdir
import importlib.util

_module_cache = {}


def get_names():
    """:return: A list of available launchers."""
    launcher_names = []

    for file in listdir(path.realpath(path.dirname(__file__))):
        if not file.endswith(".py") or file in ["__init__.py", "helper.py"]:
            continue
        else:
            launcher_names.append(file.replace(".py", "", 1))

    return launcher_names


def _load_module(module_name: str):
    """Loads the module and adds it to the cache."""
    try:
        # "One might think that python imports are getting more and more complicated with each new version."
        # Taken from https://stackoverflow.com/a/67692
        module_path = path.realpath(path.join(path.dirname(__file__), module_name + ".py"))
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)
        _module_cache[module_name] = module

        return module
    except FileNotFoundError:
        raise ImportError("Failed to find launcher: {}".format(module_name)) from None


def generate(launcher_name: str, stager: str) -> tuple:
    """:return: A tuple containing the file extension and code of this launcher."""
    cached_launcher = _module_cache.get(launcher_name)

    if cached_launcher:
        return cached_launcher.Launcher().generate()
    else:
        return _load_module(launcher_name).Launcher().generate(stager)


_module_cache["helper"] = _load_module("helper")
