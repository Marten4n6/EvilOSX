class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "This is an example module.",
            "References": [
                # External links related to this module.
                "http://example.com/"
            ],
            "Task": False  # True if this module should be run in the background.
        }
        self.example_message = None

    def setup(self, module_view, output_view, successful):
        """This method is called before a module is sent, used to set variables.

        :param module_view The module view to interact with.
        :param successful successful.put(True) if the setup was successful.
        :type successful Queue.Queue
        """
        self.example_message = module_view.prompt("Message to print: ")
        successful.put(True)

    def run(self):
        """This is the code which gets executed on the client."""
        return """\
        print "Example message: %s"
        """ % self.example_message

    def process_response(self, output_view, response):
        """Optional method which processes the response."""
        output_view.add_line(response.replace("Example message", "Processed example message"), "info")
