#!/usr/bin/env python

from distutils.core import setup

setup(name='virtualee',
      version='2.0',
      description='Client for eie-virtual site',
      author='Alexander Marin',
      author_email='alexanderm2230@gmail.com',
      url='',
      scripts=['virtualee'],
      package_dir={'virtualee': ''},
      packages=['virtualee', 'virtualee.gui', 'virtualee.lib'],
      data_files=[('/usr/share/applications', ['virtualee.desktop']),
                  ('/usr/share/pixmaps', ['gui/icons/logo_virtualee.png'])],
      package_data={'virtualee': ['gui/sign_in_img.png', 'gui/virtualee.png', 'conf.json']},
      requires=['requests', 'bs4', 'keyring', 'pyside']
      )

