class Loader:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "This is an example loader.",
            "References": [],
        }

    def setup(self):
        """:return A dictionary containing configuration options (with the launcher name as the key).

        This method is optional, called by the builder before creating a stager.
        """
        return {"template": {"example_key": "This is an example value."}}

    def generate(self, payload, options):
        """Generates the loader which decides how the payload will be loaded by the stager."""
        return """\
        # Value of "example_key": %s
        
        %s
        """ % (options["example_key"], payload)

    def remove_payload(self):
        """Removes the payload."""
        pass

    def update_payload(self, server_host, server_port):
        """Updates the payload to a new server host/port."""
        pass
