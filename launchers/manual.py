class Launcher:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Creates a manual launcher.",
            "References": [],
        }

    def generate(self, stager):
        return ("", """\
        %s
        """ % stager)
