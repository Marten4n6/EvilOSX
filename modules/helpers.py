from abc import ABCMeta, abstractclassmethod


class ModuleABC(metaclass=ABCMeta):
    """Abstract base class for modules."""

    @abstractclassmethod
    def get_info(self) -> dict:
        """:return A dictionary containing information about this module."""
        pass

    @abstractclassmethod
    def setup(self, module_input, view, successful):
        """Handles any required user input."""
        pass

    @abstractclassmethod
    def run(self) -> str:
        """:return The code to be executed on the client."""
        pass

    def process_response(self, response: bytes, view):
        """Optional method to override, handles the response."""
        self._output_response(response, view)

    def _output_response(self, response: bytes, view):
        """Sends the response to the output view."""
        view.output_separator()

        response = response.decode()  # From here on we need a str not bytes.

        if "\n" in response:
            for line in response.splitlines():
                view.output(*self._get_prefix_type(line))
        else:
            view.output(*self._get_prefix_type(response))

    @staticmethod
    def _get_prefix_type(line: str) -> tuple:
        """:return A tuple containing the clean line and prefix type."""
        message_info = "\033[94m" + "[I] " + "\033[0m"
        message_attention = "\033[91m" + "[!] " + "\033[0m"

        if line.startswith(message_info):
            return line.replace(message_info, "", 1), "info"
        elif line.startswith(message_attention):
            return line.replace(message_attention, "", 1), "attention"
        else:
            return line, ""
