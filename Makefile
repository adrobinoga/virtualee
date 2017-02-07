build: dialogs
	python setup.py --command-packages=stdeb.command bdist_deb

dialogs:
	cd gui; make gui

install: build
	cd deb_dist; sudo dpkg -i 
