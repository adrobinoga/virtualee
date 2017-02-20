# Virtualee
Desktop client to keep track of docs on eie virtual site.

Keeps a local copy of eie-virtual course materials on "~/eie-virtual", and when it updates the local copy, adds those events to a history file, in that way we may know if there is a recent added file, though this "recent files" may be not recent, but there is no easy way to check if docs in eie site are new. Also displays recent news from eie site and empleo-eie.

# Installation
Check for releases on <https://github.com/adrobinoga/virtualee/releases>

# Getting Started
Pyinstaller is used to build the executables, the build process must be performed from executable's target platform(Wine may help in Linux). Do it with a 32 bit system for better portability.


## Linux

### Prerequisites
First, we must install all the packages needed to get the program running without frezeeing it.

$ sudo apt-get install python-pip

$ pip install requests keyring pyside bs4

### Build

$ sudo apt-get install pyside-tools

Then we are ready to freeze the app

$ sudo apt-get install pyqt4-dev-tools python-stdeb # need this to build

$ make build

This step actually parses ui files to py and then runs pyinstaller.

This will generate a Linux executable on dist folder.

## Windows

### Prerequisites
First we must install all the packages needed to get the program running without frezeeing it.

Get python2.7(Set add-to-Path option!) from 

<https://www.python.org/downloads/windows/>

Install next python modules

\> pip install keyring requests pyside bs4

Then install lxml(lxml‑3.7.2‑cp27‑cp27m‑win32.whl) from

<http://www.lfd.uci.edu/~gohlke/pythonlibs/>


### Build
Assuming that our folder is shared and that we generated the gui files previously on a Linux system, with:

$make dialogs

We may skip to freezeing the app, first we need to install pyinstaller:

\> pip install pyinstaller

Then freeze the app:

\> pyinstaller virtualee_pkg.spec

This will generate an Windows executable on dist folder.

# Todo
 - Enable periodic update of materials and display notifications with pynotify.
 - Display agenda and comments from eie-virtual dashboard.

# Author

Alexander Marin <alexanderm2230@gmail.com>

# License

This project is licensed under the GNU GENERAL PUBLIC LICENSE Version 3

