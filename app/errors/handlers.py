'''
app/errors/handlers.py
Created by Shivangi Sritharan
Last modified: 18/04/2026

This file contains custom error handlers.
'''

from flask import render_template, flash, redirect, url_for, jsonify, request

# 404 page not found
def page_not_found(e):
    return render_template("errors/404.html", title='404 Page Not Found'), 404

def ratelimit_exceeded(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="rate_limit_exceeded", message="Too many requests. Please slow down."), 429
    flash("Too many requests. Please slow down.", "warning")  # ✅ just call it alone
    return redirect(url_for('main.index'))

# 500 internal server error
def internal_error(error):
    #db.session.rollback() # only useful if error was caused by a database mismatch
    return render_template('errors/500.html'), 500

