'''
app/help/routes.py
Created by Shivangi Sritharan
Last modified: 18/04/2026

This file contains the routes for the help
pages in the application.
'''

from flask import render_template
from app.help import help_bp

# route for help page
@help_bp.route('/') # this acts as an index page for the help pages (see blueprint registration in app/__init__.py)
def help_index(): # can't name this help because it would shadow python's built-in help function
    return render_template('help/help.html', title='Help')

# route for SLSL finger spelling chart
@help_bp.route('/slslchart')
def slslchart():
    return render_template('help/slslchart.html', title='SLSL Chart')

# route for video tutorial
@help_bp.route('/video-tutorial')
def video_tutorial():
    return render_template('help/video-tutorial.html', title='Video Tutorial')

# route for user guide
# not implemented yet!
