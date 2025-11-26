# Lord of the Rings Online Linux Utilities

I got tired of searching for my Proton prefix and setting up shell variables to install plugins or update the Music folder, so I wrote this small set of utilities for running Lord of the Rings Online on Linux. So far, the capabilities extend to:

- Running a multibox setup (currently configured for six characters)
- Installing plugins
- Updating the Music database (a la Songbooker, for musicians)

Usage:
python3 main.py

## In Progress / TODO

- Setting up keychains / credential stores for multibox auto-login
- User-customizable multibox parameters (characters, keystore, etc.)

## Testing

This has been tested both on a desktop daily driver, as well as on my Steam Deck. I've added some rudimentary porting for Windows on the Music database update pieces of the code, but haven't extended that to plugin installation, keyrings, etc. If there is a heavy demand for Windows integration, please let me know so I can spin up a VM and continue the platform port.