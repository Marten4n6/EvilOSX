from launchers.helpers import LauncherABC


class Launcher(LauncherABC):
    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Creates a manual launcher.",
            "References": [],
        }

    def generate(self, stager: str):
        return ("", """\
        {}
        """.format(stager))
