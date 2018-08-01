# -*- coding: utf-8 -*-
"""Creates modules using the factory pattern."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import imp
from os import path, listdir
from typing import Optional
from zlib import compress

from server.modules.helper import ModuleABC

_module_cache = {}


def load_module(module_name, view, model):
    """Loads the loader and adds it to the cache.

    :type module_name: str
    """
    # Going to use imp over importlib until python decides to remove it.
    module_path = path.realpath(path.join(path.dirname(__file__), "server", module_name + ".py"))
    module = imp.load_source(module_name, module_path)

    _module_cache[module_name] = module.Module(view, model)

    return _module_cache[module_name]

def get_module(module_name):
    """
    :type module_name: str
    :rtype: ModuleABC or None
    :return: The module class if it has been loaded, otherwise None.
    """
    return _module_cache.get(module_name)


def get_names():
    """
    :rtype: list[str]
    :return: A list of all module names."""
    names = []

    for name in listdir(path.realpath(path.join(path.dirname(__file__), "server"))):
        if name.endswith(".py") and name not in ["__init__.py", "helper.py"]:
            names.append(name.replace(".py", ""))

    return names


def get_code(module_name):
    """
    :type module_name: str
    :rtype: bytes
    :return: Compressed code which can be run on the bot.
    """
    source_path = path.realpath(path.join(path.dirname(__file__), "bot", module_name + ".py"))

    with open(source_path, "rb") as input_file:
        code = input_file.read()

    return compress(code)
