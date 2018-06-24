# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from abc import ABCMeta, abstractmethod
from queue import Queue
from threading import Lock
from threading import current_thread

import urwid


class OutputViewABC(metaclass=ABCMeta):
    """Abstract base class for the output view."""

    @abstractmethod
    def add(self, line: str, style: str = ""):
        """Adds a line to the output view."""
        pass

    @abstractmethod
    def clear(self):
        """Clears the output view."""
        pass


class ViewABC(metaclass=ABCMeta):
    """Abstract base class for views."""

    @abstractmethod
    def output(self, line: str, prefix: str = ""):
        """Adds a line to the view."""
        pass

    @abstractmethod
    def output_separator(self):
        """Adds a separator to the view."""
        pass

    @abstractmethod
    def prompt(self, prompt_text: str, lines: list = None) -> str:
        """Prompts for user input, assumes the caller isn't on the main thread.

        :param prompt_text: The prompt text shown to the user.
        :param lines: A list of tuples containing each line and prefix.
        """

    @abstractmethod
    def set_on_command(self, callback_function):
        """Registers the command listener."""
        pass

    @abstractmethod
    def set_header_text(self, text: str):
        """Sets the header text."""
        pass

    @abstractmethod
    def set_footer_text(self, text: str):
        """Sets the footer text."""
        pass

    @abstractmethod
    def clear(self):
        """Clears the output view."""
        pass

    @abstractmethod
    def start(self):
        """Initializes the view."""
        pass


class OutputView(OutputViewABC):
    """Default OutputABC implementation."""

    def __init__(self, max_size: int = 69):
        self._max_size = max_size

        self._output_view = urwid.ListBox(urwid.SimpleListWalker([]))
        self._lock = Lock()

        self._main_loop = None

    def get(self) -> urwid.ListBox:
        return self._output_view

    def set_main_loop(self, main_loop):
        self._main_loop = main_loop

    def add(self, line: str, prefix: str = ""):
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


class CommandInput(urwid.Pile):
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

    def set_header_text(self, text: str):
        with self._lock:
            self._header.set_text(text)

    def add(self, line: str, prefix: str = ""):
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

    def get_prompt_input(self) -> str:
        with self._lock:
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

        self._header = urwid.Text("")
        self._output_view = OutputView()
        self._command_input = CommandInput()

        self._main_loop = None

        # Initialize the frame.
        self._frame = urwid.Frame(
            header=urwid.AttrWrap(self._header, "reversed"),
            body=self._output_view.get(),
            footer=self._command_input
        )

        self._frame.set_focus_path(["footer", 2])

    def output(self, line: str, prefix: str = ""):
        self._output_view.add(line, prefix)

    def output_separator(self):
        self.output(self._SEPARATOR)

    def prompt(self, prompt_text: str, lines: list = None) -> str:
        if lines:
            for line in lines:
                self._command_input.add(*line)
        self._command_input.add(prompt_text, "input")

        return self._command_input.get_prompt_input()

    def set_on_command(self, callback_function):
        # See http://urwid.org/reference/signals.html
        urwid.connect_signal(self._command_input, "line_entered", callback_function)

    def set_header_text(self, text: str):
        self._header.set_text(text)
        self._async_reload()

    def set_footer_text(self, text: str):
        self._command_input.set_header_text(text)
        self._async_reload()

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