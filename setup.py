#!/usr/bin/env python

from distutils.core import setup

setup(name='virtualee',
      version='1.0',
      description='Client for eie-virtual site',
      author='Alexander Marin',
      author_email='alexanderm2230@gmail.com',
      url='',
      scripts=['virtualee'],
      py_modules=['lib.scrapeie', 'lib.verctrl', 'lib.histdocs', 'gui.Sign_In',
                  'gui.About', 'gui.Pref', 'gui.Virtualee', 'gui.icons_rc'],
      data_files=[('/usr/share/applications', ['virtualee.desktop']),
                  ('/usr/share/pixmaps', ['gui/logo_virtualee.png']),
                  ('/usr/share/virtualee', ['gui/sign_in_img.png', 'gui/virtualee.png', 'conf.json'])],
      requires=['requests', 'bs4', 'keyring', 'PyQt4']
      )

