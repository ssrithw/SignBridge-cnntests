'''
routes.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains the routes every web page in this
application. It reuses code from the deprecated app.py but
is part of the new modularization effort.
'''

from flask import render_template, redirect, url_for
from flask_login import current_user
from app.main import main_bp

# route for landing page
@main_bp.route('/')
@main_bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('user.profile'))
    return render_template('main/index.html', title='Landing')

# route for about page
@main_bp.route('/about')
def about():
    return render_template('main/about.html', title='About Us')

# route for contact page
@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html', title='Contact Us')