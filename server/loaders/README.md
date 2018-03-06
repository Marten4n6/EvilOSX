Since EvilOSX is loaded into memory by the stager, it can't move itself to become persistent (```__file__``` won't work). <br/>
Loaders are the solution to this problem, these are given the encrypted payload and decide how the payload will be loaded by the stager.

It's important that the loader sends the payload to the background (since launchers don't do this).