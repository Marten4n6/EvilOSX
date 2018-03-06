class Launcher:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "This is an example launcher.",
            "References": [],
        }

    def generate(self, stager):
        """Generates the launcher whose only goal is to run the stager code.

        In this example because we don't specify a file extension in the tuple the
        stager will just be printed to the screen.
        """
        return ("", """\        
        %s
        """ % stager)
