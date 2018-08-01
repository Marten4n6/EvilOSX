<h1 align="center">
  Modules
  <br>
</h1>

<h4 align="center">Modular programming is a software design technique that emphasizes separating the functionality of a program into independent, interchangeable modules, such that each contains everything necessary to execute only one aspect of the desired functionality.</h4>

---

## Creating a module
Modules are split up into two files.

### Server
For this example we're going to create a simple module which says "Hello world!" to the bot (via text to speech). <br/>
The first file should be under the [server](https://github.com/Marten4n6/EvilOSX/tree/master/server/modules/server) directory (I called mine **say.py**).

We can use this to get information, setup and process the response of a module. <br/>
This file will be automatically picked up by the server if we follow the rules specified in the ModuleABC class. <br/>
Here's how the server side of this module looks: <br/>
```python
from server.modules.helper import *


class Module(ModuleABC):
    def get_info(self):
        return {
            "Author:": ["Marten4n6"],
            "Description": "Speak to the bot via text to speech.",
            "References": [],
            "Stoppable": False
        }

     def get_setup_messages():
        """Setup messages which will be presented to the user.

        In this example we'll ask the user for the message they want
        text to speech to speak to the bot.
        """
        return [
            "Message to speak (Leave empty for \"Hello world!\"): "
        ]

    def setup(self, set_options):
        """Called after all options have been set."""
        message = set_options[0]

        if not message:  # The user pressed enter, set the default.
            message = "Hello world!"

        # Return True to indicate the setup was successful.
        # This dictionary will be sent to the bot side of this module.
        return True, {
            "message": message
        }
```
Now this module will be picked up by the server (you can see this by starting the server and typing "modules"). <br/>

### Bot
Now let's make our module actually do something...

The second file should be under the [bot](https://github.com/Marten4n6/EvilOSX/tree/master/server/modules/bot) directory and named the same as the server side. <br/>
Every module must contain the following function:
```python
def run(options):
    # This is the required starting point of every module.
    pass
 ```
The optional dictionary returned by the setup method (of the first file) is passed to this function. <br/>
It's useful to know that this dictionary always contains the following keys: <br/>
```"server_host", "server_port", "program_directory"```

Anything printed by a module will **directly** be returned to the server's ```process_response``` method. <br/>
Optionally, the dictionary returned by the server's ```setup``` method may have a "response_options" key which is then also sent back to this method.

Here's the bot side of our example:
```python
import subprocess


def run(options):
    message = options["message"]

    subprocess.call("say '%s'" % message, shell=True)
    print("Say module finished!")
```

##
Feel free to submit an [issue](https://github.com/Marten4n6/EvilOSX/issues) or send me an email if you have any further questions.