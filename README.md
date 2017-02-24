# Virtualee
Desktop client to keep track of docs on eie virtual site.

Keeps a local copy of eie-virtual course materials on "~/eie-virtual", and when it updates the local copy, adds those events to a history file, in that way we may know if there is a recent added file, though this "recent files" may be not recent, but there is no easy way to check if docs in eie site are new. Also displays recent news from eie site and empleo-eie.

# Installation
Check for releases in <https://github.com/adrobinoga/virtualee/releases>

# Getting Started
Stdeb is used to generate a debian package and
Pyinstaller is used to build executables for nt systems, the build process must be performed in executable's target platform(Do it with a 32 bit system for better portability).


## Linux

### Prerequisites

$ sudo apt-get install python-pip pyside-tools

$ pip install keyring requests pyside bs4

Parse ui files with

$ make dialogs

Then you may run it with

$ ./virtualee.py

Note: virtualee file is used for deb package.

### Build

To generate deb package install python-stdeb

$ sudo apt-get install python-stdeb

Then build

$ make build

This step actually parses ui files to py and then runs bdist_deb commant to generate the debian package.

deb package will be in deb_dist folder.


## Windows

### Prerequisites

First we must install all the packages needed to get the program running without frezeeing it.

Get python2.7(Set add-to-Path option!) from 

<https://www.python.org/downloads/windows/>

Install next python modules

\> pip install keyring requests pyside bs4

Then install lxml(lxml‑3.7.2‑cp27‑cp27m‑win32.whl) from

<http://www.lfd.uci.edu/~gohlke/pythonlibs/>

Before parsing ui files, you need to install GnuWin and add make path to the Path variable.

And must append the following path to Path variable

C:\Python27\Lib\site-packages\PySide

Then parse ui files

\> cd gui

\> make dialogs

Now you may run the program with

\> virtualee.py

### Build

First we need to install pyinstaller

\> pip install pyinstaller

Then freeze the app

\> pyinstaller virtualee_pkg.spec

This will generate an Windows executable on dist folder.

# Todo
 - Enable periodic update of materials and display notifications with pynotify.
 - Display agenda and comments from eie-virtual dashboard.

# Author

Alexander Marin Drobinoga <alexanderm2230@gmail.com>

# License

This project is licensed under the GNU GENERAL PUBLIC LICENSE Version 3

