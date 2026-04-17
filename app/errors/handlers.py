'''
handlers.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

Errors go here (add proper desc)
dulneth pls look at this
'''

from flask import render_template, flash, redirect, url_for

# 404 page not found
def page_not_found(e):
    return render_template("errors/404.html", title='404 Page Not Found'), 404

# 429 rate limit exceeded
def ratelimit_exceeded(e):
    flash("Too many requests. Please slow down.", "warning")
    return redirect(url_for('/')), 302 # temporary redirect

# 500 internal server error
def internal_error(error):
    #db.session.rollback() # only useful if error was caused by a database mismatch
    return render_template('errors/500.html'), 500