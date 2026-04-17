'''
routes.py
Created by Shivangi Sritharan
Last modified: 17/04/2026

This file contains the routes every web page in this
application. It reuses code from the deprecated app.py but
is part of the new modularization effort.
'''

from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlsplit # used to redirect logged out users
import sqlalchemy as sa
from extensions import db, limiter
from app.models import User
from app.auth import auth_bp
from app.auth.forms import LoginForm, SignupForm, ResetPasswordRequestForm, ResetPasswordForm
from app.auth.email import send_password_reset_email

# route for login page
@auth_bp.route('/login', methods=['GET', 'POST']) # define http methods to send and receive data
@limiter.limit("5 per minute")
def login():
    # if user is authenticated, stop them from navigating back to login
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    # if not authenticated, go to login
    form = LoginForm()
    if form.validate_on_submit(): # validate all data before allowing submit
        # since this is login, compare form data with list of registered users
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        # if username or password are incorrect, try again
        if user is None or not user.check_password(form.password.data):
            current_app.logger.warning(f"Failed login attempt for username: {form.username.data} from IP: {request.remote_addr}")
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        # if remember me is ticked, save that too
        login_user(user, remember=form.remember_me.data)
        current_app.logger.info(f"User {user.username} logged in from IP: {request.remote_addr}")
        # check for last accessed page
        next_page = request.args.get('next')
        # specifically, check if it's not a relative path or is a full domain (ie. if you're accessing from pizzahut.lk, don't redirect back there)
        if not next_page or urlsplit(next_page).netloc != '':
            # redirect to landing page
            next_page = url_for('main.index')
        # redirect to whatever is in next_page
        return redirect(next_page)
    return render_template('auth/login.html', title='Log In', form=form)

# route for logout
@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        current_app.logger.info(f"User {current_user.username} has logged out.")
    logout_user()
    return redirect(url_for('main.index'))

# route for registration page
@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"New user registered. Username: {user.username} and email: ({user.email})")
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

# reset password request
@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = db.session.scalar(sa.select(User).where(User.email == email))
        current_app.logger.info(f"Password reset requested for email: {email} from IP: {request.remote_addr}")
        if user:
            send_password_reset_email(user)
            current_app.logger.info(f"Reset email sent to user_id={user.id}")
        # note that this message is sent regardless of whether an email
        # was actually sent or not - this is to prevent users from
        # figuring out if an email is registered or not
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

# reset actual password
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
@limiter.limit('3 per minute')
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        current_app.logger.warning(f"Invalid or expired reset token used from IP: {request.remote_addr}")
        flash('Invalid or expired reset link.')
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # stop users from reusing old password
        if user.check_password(form.password.data):
            current_app.logger.info(f"User tried reusing old password: user_id={user.id}")
            flash('Please choose a different password.')
            return redirect(url_for('auth.reset_password', token=token))
        user.set_password(form.password.data)
        db.session.commit()
        current_app.logger.info(f"Password successfully reset for user_id={user.id}")
        flash('Your password has been reset. You can now log in.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)