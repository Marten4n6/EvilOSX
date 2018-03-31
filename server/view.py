#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interacts with the user via urwid, uses the MVC pattern (using signals)."""
__author__ = "Marten4n6"
__license__ = "GPLv3"

import urwid
from abc import ABCMeta, abstractclassmethod
from threading import Lock, RLock
from queue import Queue
from threading import current_thread


class OutputViewABC(metaclass=ABCMeta):
    """Abstract base class for the output view."""

    @abstractclassmethod
    def add(self, line: str, style: str = ""):
        """Adds a line to the output view."""
        pass

    @abstractclassmethod
    def clear(self):
        """Clears the output view."""
        pass


class ModuleInputABC(metaclass=ABCMeta):
    """Abstract base class for module input (which modules use to interact with the user)."""

    @abstractclassmethod
    def add(self, line: str, prefix: str = ""):
        """Adds a line to the input view."""
        pass

    @abstractclassmethod
    def clear(self):
        """Clears the input view."""
        pass

    @abstractclassmethod
    def prompt(self, message: str) -> str:
        """Prompts for user input."""
        pass


class ViewABC(metaclass=ABCMeta):
    """Abstract base class for views."""

    @abstractclassmethod
    def output(self, line: str, prefix: str = ""):
        """Adds a line to the view."""
        pass

    @abstractclassmethod
    def output_separator(self):
        """Adds a separator to the view."""
        pass

    @abstractclassmethod
    def set_on_command(self, callback_function):
        """Registers the command listener."""
        pass

    @abstractclassmethod
    def set_header_text(self, text: str):
        """Sets the header text."""
        pass

    @abstractclassmethod
    def set_footer_text(self, text: str):
        """Sets the footer text."""
        pass

    @abstractclassmethod
    def get_module_input(self) -> ModuleInputABC:
        """:return The class used by modules to interact with the user."""
        pass

    def get_output_view(self) -> OutputViewABC:
        """:return The class used by modules to output messages."""
        pass

    @abstractclassmethod
    def set_module_input(self, module_name: str):
        """Switches to the module input."""
        pass

    @abstractclassmethod
    def set_command_input(self):
        """Switches to the command input."""
        pass

    @abstractclassmethod
    def clear(self):
        """Clears the output view."""
        pass

    @abstractclassmethod
    def start(self):
        """Initializes the view."""
        pass


class _ModuleInput(ModuleInputABC):
    """Default ModuleInputABC implementation."""

    def __init__(self, main_loop):
        self._main_loop = main_loop

        self._header = urwid.Text("")
        self._list = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self._layout = urwid.BoxAdapter(self._list, 0)  # Dynamically change size
        self._edit_box = urwid.Edit()

        self._queue = Queue()
        self._lock = RLock()  # It's important this is an RLock instead of a Lock
        self.previous_prompt = False

        # Initialize the pile.
        self._pile = urwid.Pile([
            urwid.AttrWrap(self._header, "reversed"),
            self._layout,
            self._edit_box
        ])

        self._edit_box.keypress = self.keypress  # !
        self._pile.focus_item = self._edit_box

    def get(self) -> urwid.Pile:
        return self._pile

    def set_header_text(self, text: str):
        self._header.set_text(text)

    def add(self, line: str, prefix: str = ""):
        with self._lock:
            # Set the height of the output list so the message is actually visible
            self._layout.height = len(self._list.body) + 1

            if prefix == "info":
                self._list.body.append(urwid.Text([("normal", "["), ("info", "I"), ("normal", "] " + line)]))
            elif prefix == "input":
                self._list.body.append(urwid.Text("[?] " + line))
            elif prefix == "attention":
                self._list.body.append(
                    urwid.Text([("normal", "["), ("attention", "!"), ("normal", "] " + line)]))
            else:
                self._list.body.append(urwid.Text(line))

            self._async_reload()

    def clear(self):
        with self._lock:
            del self._list.body[:]
            self._layout.height = 0

    def prompt(self, message: str):
        with self._lock:
            if self.previous_prompt:
                # Clear the previous prompt.
                self.clear()
            else:
                self.previous_prompt = True

            self.add(message, "input")

            # Blocks until input from keypress.
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

    def _async_reload(self):
        """Required if this method is called from a different thread asynchronously."""
        if self._main_loop and self._main_loop != current_thread():
            self._main_loop.draw_screen()


class _CommandInput(urwid.Pile):
    """This class shows the command input view."""
    signals = ["line_entered"]

    def __init__(self):
        self._header = urwid.Text("Command: ")
        self._edit_box = urwid.Edit()
        self._lock = Lock()

        urwid.Pile.__init__(self, [
            urwid.AttrWrap(self._header, "reversed"),
            self._edit_box
        ])

        self.focus_item = self._edit_box

    def set_header_text(self, text: str):
        """Sets the header text."""
        with self._lock:
            self._header.set_text(text)

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


class _OutputView(OutputViewABC):
    """Default OutputABC implementation."""

    def __init__(self, max_size: int = 1337):
        self._max_size = max_size

        self._output_view = urwid.ListBox(urwid.SimpleListWalker([]))
        self._lock = Lock()

    def get(self) -> urwid.ListBox:
        return self._output_view

    def add(self, line: str, style: str = ""):
        """Adds a line to the output view."""
        with self._lock:
            was_on_end = self._output_view.get_focus()[1] == len(self._output_view.body) - 1

            if len(self._output_view.body) > self._max_size:
                # Size limit reached, delete the first line.
                del self._output_view.body[0]

            if style == "info":
                self._output_view.body.append(urwid.Text([('normal', "["), ('info', "I"), ("normal", "] " + line)]))
            elif style == "input":
                self._output_view.body.append(urwid.Text([('normal', "["), ('reversed', "?"), ("normal", "] " + line)]))
            elif style == "attention":
                self._output_view.body.append(urwid.Text([('normal', "["), ('attention', "!"), ("normal", "] " + line)]))
            else:
                self._output_view.body.append(urwid.Text(line))

            if was_on_end:
                self._output_view.set_focus(len(self._output_view.body) - 1, "above")

    def clear(self):
        """Clears the output view."""
        with self._lock:
            del self._output_view.body[:]


class View(ViewABC):
    """This class interacts with the user.

    This is the default ViewABC implementation.
    The controller will register all listeners (set_on_*) for this view.
    """

    def __init__(self):
        self._PALETTE = [
            ("reversed", urwid.BLACK, urwid.LIGHT_GRAY),
            ("normal", urwid.LIGHT_GRAY, urwid.BLACK),
            ("info", urwid.LIGHT_BLUE, urwid.BLACK),
            ("attention", urwid.LIGHT_RED, urwid.BLACK)
        ]
        self._SEPARATOR = "-" * 5

        self._main_loop = None  # Used by async_reload and the module input.

        self._header = urwid.Text("")
        self._output_view = _OutputView()
        self._command_input = _CommandInput()
        self._module_input = None  # Initialized when the main loop starts.

        # Initialize the frame.
        self._frame = urwid.Frame(
            header=urwid.AttrWrap(self._header, "reversed"),
            body=self._output_view.get(),
            footer=self._command_input
        )

        self._frame.set_focus_path(["footer", 1])

    def output(self, line: str, prefix: str = ""):
        self._output_view.add(line, prefix)
        self._async_reload()

    def output_separator(self):
        self._output_view.add(self._SEPARATOR)
        self._async_reload()

    def set_on_command(self, callback_function):
        # See http://urwid.org/reference/signals.html
        urwid.connect_signal(self._command_input, "line_entered", callback_function)

    def set_header_text(self, text: str):
        self._header.set_text(text)

    def set_footer_text(self, text: str):
        self._command_input.set_header_text(text)

    def get_module_input(self) -> ModuleInputABC:
        return self._module_input

    def get_output_view(self) -> OutputViewABC:
        return self._output_view

    def set_module_input(self, module_name: str):
        self._frame.footer = self._module_input.get()
        self._module_input.set_header_text("Module {}: ".format(module_name))

        # Clear any previous output.
        self._module_input.clear()
        self._module_input.previous_prompt = False

    def set_command_input(self):
        self._frame.footer = self._command_input
        self._async_reload()

    def clear(self):
        self._output_view.clear()

    def start(self):
        self._main_loop = urwid.MainLoop(self._frame, self._PALETTE, handle_mouse=True)
        self._module_input = _ModuleInput(self._main_loop)

        self._main_loop.run()

    def _async_reload(self):
        """Required if a method is called from a different thread asynchronously."""
        if self._main_loop and self._main_loop != current_thread():
            self._main_loop.draw_screen()
