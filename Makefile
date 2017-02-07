build: dialogs
	python setup.py --command-packages=stdeb.command bdist_deb

dialogs:
	cd gui; make gui

