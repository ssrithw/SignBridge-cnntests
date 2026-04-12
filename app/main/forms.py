'''
forms.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains forms. Idk. Update later.
'''

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
import sqlalchemy as sa
from app import db
from app.models import User

class EditProfileForm(FlaskForm):
    username = StringField(('Username'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError(('Please use a different username.'))

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')