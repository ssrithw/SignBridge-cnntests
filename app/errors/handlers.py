'''
handlers.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

Errors go here (add proper desc)
dulneth pls look at this
'''

from flask import render_template, flash, redirect, url_for, request, jsonify
from app.errors import bp


# 404 page not found
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title='404 Page Not Found'), 404

# 429 rate limit exceeded
@bp.app_errorhandler(429)
def ratelimit_exceeded(e):
    flash("Too many requests. Please slow down.", "warning")
    return redirect(url_for('main.index')), 302 # temporary redirect

# 500 internal server error
@bp.app_errorhandler(500)
def internal_error(error):
    #db.session.rollback() # only useful if error was caused by a database mismatch
    return render_template('500.html'), 500