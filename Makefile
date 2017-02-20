build: dialogs
	pyinstaller virtualee_pkg.spec

dialogs:
	cd gui; make gui

clean:
	rm -rf build dist 
