'''
core/validators.py

Created by Dulneth Kurunduwatte
Last modified 16/04/2026

This file contains validation methods for user details.
It is considered a core file instead of either an auth or
user file due to the mix of methods.

'''
import re
import sqlalchemy as sa
from wtforms.validators import ValidationError
from extensions import db
from app.models import User

# this function is used in the user account forms to validate
# password complexity
def password_complexity(form, field):
    if not field.data:
        return  # only validate when a password is provided

    password = field.data
    errors = []

    if len(password) < 6:
        errors.append("at least 6 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("at least one uppercase letter (A-Z)")
    if not re.search(r'[a-z]', password):
        errors.append("at least one lowercase letter (a-z)")
    if not re.search(r'[0-9]', password):
        errors.append("at least one number (0-9)")
    if not re.search(r'[!@#$%^&*]', password):
        errors.append("at least one special character (!@#$%^&*)")

    if errors:
        raise ValidationError(
            "Password must include: " + ", ".join(errors) + "."
        )
    
# the functions below are used to check the uniqueness of a
# username or email when creating an account or editing
# your profile.
# however, the requirements of each form is slightly 
# different - the create account form checks for a 
# username that doesn't exist, whereas the edit user
# form must let the user keep their current username.
# I've implemented a factory that checks if the value is
# taken and returns values accordingly
def unique_username(original=None): # pass original to skip the uniqueness check if value is unchanged

    def validator(form, field):
        if original and field.data == original:
            return 
        user = db.session.scalar(sa.select(User).where(User.username == field.data))
        if user is not None:
            raise ValidationError('This username is taken! Please use a different username.')
    return validator


def unique_email(original=None): # pass original to skip the uniqueness check if value is unchanged
    def validator(form, field):
        if original and field.data == original:
            return
        user = db.session.scalar(sa.select(User).where(User.email == field.data))
        if user is not None:
            raise ValidationError('This email is taken! Please use a different email address.')
    return validator
