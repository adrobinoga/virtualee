# virtualee
Desktop client to keep track of docs and news on eie virtual site

May download all materials from website or just download materials that doesn't exist on local copy(~/eie-virtual), and when it updates adds those events to a history file, in that way we may know if there is a recent added file, this approach have the drawback that this "recent files" may be not recent, but there is no easy way to check if docs in eie site are new.

# Todo
 - Remove criteria option in history or use sqlite.
 - Use threads.
 - Enable periodic update of materials and display notifications with pynotify.
 - Display agenda and comments from eie-virtual dashboard.

# Installation
Download repo

$ git clone https://github.com/adrobinoga/virtualee.git

Install

$ cd virtualee

$ sudo apt-get install pyqt4-dev-tools python-stdeb # need this to build

$ make build

Then .deb file is on deb_dist/

$ cd deb_dist

$ sudo dpkg -i python-virtualee_1.0-1_all.deb

To uninstall 

$ sudo dpkg -P python-virtualee

# Author
Alexander Marin <alexanderm2230@gmail.com>
