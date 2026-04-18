'''
app/user/forms.py
Created by Shivangi Sritharan
Last modified: 18/04/2026

This file contains user-related forms that
are not related to authentication.
Forms are implemented with WTForms.
'''

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import ValidationError, Email, EqualTo, Optional
from flask_login import current_user
from app.models import User
from app.core.validators import password_complexity, unique_email, unique_username

class EditProfileForm(FlaskForm):
    # username field
    username = StringField(('Change your username:'), 
        validators=[Optional()],
        # render_kw tells the application how to render the form with CSS
        render_kw={"class": "input", "placeholder": "Username"}
    )

    # email field
    email = StringField(('Change your e-mail:'), 
        validators=[Optional(), Email()],
        render_kw={"class": "input", "placeholder": "E-mail"}
    )

    # password fields 
    current_password = PasswordField(('Enter your current password:'),
        validators=[Optional()],
        render_kw={"class": "input", "placeholder": "Password"}
    )

    new_password = PasswordField(('Enter your new password:'),
        validators=[Optional(), password_complexity],
        render_kw={"class": "input", "placeholder": "New Password"}
    )

    repeat_new_password = PasswordField(
        'Repeat your new password:', 
        validators=[Optional(), EqualTo('new_password', message='Passwords must match.')],
        render_kw={"class": "input", "placeholder": "Repeat New Password"}
    )

    submit = SubmitField(('Submit'))


    def __init__(self, original_username, original_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        
        # pass original values to skip the uniqueness check in validators.py if value is unchanged
        self.username.validators = [*self.username.validators, unique_username(original_username)]
        self.email.validators = [*self.email.validators, unique_email(original_email)]
            
    # used to validate password data        
    def validate(self, extra_validators=None):
        # check if there's data in either of the new password fields
        if self.new_password.data or self.repeat_new_password.data:

            if not self.current_password.data:
                self.current_password.errors.append(
                    "Enter your current password to set a new one."
                )
                return False

            if not current_user.check_password(self.current_password.data):
                self.current_password.errors.append(
                    "Current password is incorrect."
                )
                return False

            # ensure both password fields exist together
            if not self.new_password.data or not self.repeat_new_password.data:
                self.new_password.errors.append(
                    "Both password fields are required."
                )
                return False

        return super().validate(extra_validators)

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')