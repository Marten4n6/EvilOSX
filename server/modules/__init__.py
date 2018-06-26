# -*- coding: utf-8 -*-
"""Creates modules using the factory pattern."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import importlib.util
from os import path, listdir
from typing import Optional
from zlib import compress

from server.modules.helper import ModuleABC

_module_cache = {}


def load_module(module_name: str, view, model) -> ModuleABC:
    """Loads the module and adds it to the cache."""
    try:
        # "One might think that python imports are getting more and more complicated with each new version."
        # Taken from https://stackoverflow.com/a/67692
        module_path = path.realpath(path.join(path.dirname(__file__), "server", module_name + ".py"))
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)
        _module_cache[module_name] = module.Module(view, model)

        return _module_cache[module_name]
    except FileNotFoundError:
        raise ImportError("Failed to find module: {}".format(module_name)) from None


def get_module(module_name: str) -> Optional[ModuleABC]:
    """:return: The module class if it has been loaded, otherwise None."""
    return _module_cache.get(module_name)


def get_names() -> list:
    """:return: A list of all module names."""
    names = []

    for name in listdir(path.realpath(path.join(path.dirname(__file__), "server"))):
        if name.endswith(".py") and name not in ["__init__.py", "helper.py"]:
            names.append(name.replace(".py", ""))

    return names


def get_code(module_name: str) -> bytes:
    """:return: Compressed code which can be run on the bot."""
    source_path = path.realpath(path.join(path.dirname(__file__), "bot", module_name + ".py"))

    with open(source_path, "rb") as input_file:
        code = input_file.read()

    return compress(code)
