'''
routes.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains the routes every web page in this
application. It reuses code from the deprecated app.py but
is part of the new modularization effort.
'''

from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
import sqlalchemy as sa
from extensions import db
from app.user.forms import EditProfileForm, EmptyForm
from app.models import User
from app.user import user_bp

# route for user profile page
@user_bp.route('/profile')
@login_required # for obvious reasons
def profile():
    form = EmptyForm()
    return render_template('user/user.html', title='Your Account', user=current_user, form=form)

# route for edit user page
@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required # for obvious reasons
def edit_profile():
    form = EditProfileForm(current_user.username, current_user.email)

    if form.validate_on_submit():
        # update username/email
        if form.username.data:
            current_user.username = form.username.data

        if form.email.data:
            current_user.email = form.email.data

        # update password if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)

        db.session.commit()

        flash("Profile updated successfully")

        return redirect(url_for('user.profile'))

    return render_template('user/edit-profile.html', title='Edit Profile', form=form)
