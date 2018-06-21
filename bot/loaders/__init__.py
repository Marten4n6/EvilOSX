# -*- coding: utf-8 -*-
"""Creates loaders using the factory pattern."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import importlib.util
from os import path, listdir
from zlib import compress

_loader_cache = {}


def _load_loader(loader_name: str):
    """Loads the loader and adds it to the cache."""
    try:
        # "One might think that python imports are getting more and more complicated with each new version."
        # Taken from https://stackoverflow.com/a/67692
        module_path = path.realpath(path.join(path.dirname(__file__), loader_name, "loader.py"))
        spec = importlib.util.spec_from_file_location(loader_name, module_path)
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)
        _loader_cache[loader_name] = module.Loader()

        return _loader_cache[loader_name]
    except FileNotFoundError:
        raise ImportError("Failed to find loader: {}".format(loader_name)) from None


def get_names() -> list:
    """:return: A list of all loader names."""
    names = []

    for name in listdir(path.realpath(path.dirname(__file__))):
        directory_path = path.realpath(path.join(path.dirname(__file__), name))

        if path.isdir(directory_path) and name not in ["__pycache__"]:
            names.append(name)

    return names


def get_info(loader_name: str) -> dict:
    """:return: A dictionary containing basic information about the loader."""
    cached_loader = _loader_cache.get(loader_name)

    if not cached_loader:
        cached_loader = _load_loader(loader_name)

    try:
        return cached_loader.get_info()
    except AttributeError:
        raise AttributeError("The module \"{}\" is missing the get_info function!".format(module_name)) from None


def get_options(loader_name: str) -> dict:
    """:return: A dictionary containing the loader's configuration options."""
    cached_loader = _loader_cache.get(loader_name)

    try:
        if cached_loader:
            return cached_loader.setup()
        else:
            return _load_loader(loader_name).setup()
    except AttributeError:
        # This loader doesn't require any setup, no problem.
        return {}


def get_remove_code(loader_name: str) -> bytes:
    """:return: Compressed code which can be run on the bot."""
    source_path = path.realpath(path.join(path.dirname(__file__), loader_name, "remove.py"))

    with open(source_path, "rb") as input_file:
        code = input_file.read()

    return compress(code)