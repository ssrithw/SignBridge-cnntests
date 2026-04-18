from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
import sqlalchemy as sa
from extensions import db, limiter
from app.user.forms import EditProfileForm, EmptyForm
from app.models import User
from app.admin import admin_bp

# route for user profile page
@admin_bp.route('/profile')
@login_required # for obvious reasons
def profile():
    form = EmptyForm()
    return render_template('user/user.html', title='Your Account', user=current_user, form=form)