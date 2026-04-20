'''
wsgi.py

Created by
Last modified

This is used to launch the application on Render.

signbridge.py has been kept as some contributors prefer
testing on a development server before pushing to
production.
'''

from gevent import monkey
monkey.patch_all()

from app import create_app

app = create_app()