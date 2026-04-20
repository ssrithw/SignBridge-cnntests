'''
app/auth/routes.py
Created by Shivangi Sritharan
Last modified: 18/04/2026

This file contains the code for authentication 
related page routes.
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
from flask_limiter.util import get_remote_address

# this variable is used to track failed login attempts
MAX_LOGIN_ATTEMPTS = 10

# since rate limit by ip is abusable when logging in
def login_key():
    username = request.form.get("username")
    if username:
        return f"login:{username.lower().strip()}" # prevents case sensitivity abuse
    return get_remote_address()

# check if user is blocked before accessing pages
@auth_bp.before_app_request
def check_if_blocked():
    if current_user.is_authenticated and current_user.is_blocked:
        logout_user()
        flash("Your account has been blocked. Contact an admin (admin.signbridge+support@gmail.com).")
        return redirect(url_for('auth.login'))

# route for login page
@auth_bp.route('/login', methods=['GET', 'POST']) # define http methods to send and receive data
@limiter.limit("5 per minute", key_func=login_key, methods=['POST'])
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
        
        # behaviour differs depending on whether the user exists or not
        if user:
            # implementing blocking functionality
            if user.is_blocked:
                flash('Your account has been blocked. Contact an admin (admin.signbridge+support@gmail.com).')
                return redirect(url_for('auth.login'))
            
            # add failed login attempts
            if not user.check_password(form.password.data):
                # For non-admin users, track failed attempts and block if necessary.
                # This prevents an admin from being locked out of the system. - Dulneth
                if not user.is_admin:
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                        user.is_blocked = True
                        current_app.logger.warning(f"User {user.username} has been blocked due to too many failed logins.")
                    db.session.commit()

                current_app.logger.warning(f"Failed login attempt for username: {form.username.data} from IP: {request.remote_addr}")
                flash('Invalid username or password')
                return redirect(url_for('auth.login'))
            
            # if successful, wipe the failed login attempts
            user.failed_login_attempts = 0
            db.session.commit()

        # if user doesn't exist
        else:
            current_app.logger.warning(f"Failed login attempt for username {form.username.data} from IP {request.remote_addr}: User does not exist")
            flash('Invalid username or password')
            # direct back to login
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
@limiter.limit("5 per minute", methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data.lower().strip()) # normalize email
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
        except sa.exc.IntegrityError:
            db.session.rollback()
            flash('Username or email already exists.')
            return redirect(url_for('auth.register'))
        current_app.logger.info(f"New user registered. Username: {user.username} and email: ({user.email})")
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

# reset password request
@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=['POST'])
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
@limiter.limit('3 per minute', methods=['POST'])
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

'''
# testing limiter remove later
from extensions import csrf

@auth_bp.route("/rate-limit-test", methods=["POST"])
@csrf.exempt
@limiter.limit("5 per minute")
def rate_limit_test():
    print("ROUTE HIT")
    print("IP:", request.headers.get("X-Forwarded-For"), request.remote_addr)
    return {"ok": True}

'''