'''
forms.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains forms. Idk. Update later.
'''

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User

# signup form - requires an email, id is indexed on email.
# uses WTForms' Email validator and consequently the email-validator package.
# todo use check_deliverability and allow_empty_local
# add error messages maybe
class SignupForm(FlaskForm):
    email = StringField(
        validators=[DataRequired(), Email()],
        render_kw={"class": "input", "placeholder": "E-mail"}
    )

    username = StringField(
        'Username', 
        validators=[DataRequired()],
        render_kw={"class": "input", "placeholder": "Username"}
        )
    
    password = PasswordField(
        'Password', 
        validators=[DataRequired()],
        render_kw={"class": "input", "placeholder": "Password"}
        )
    # repeat password
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')],
        render_kw={"class": "input", "placeholder": "Password"}
        )
    
    submit = SubmitField(
        'Sign Up',
        render_kw={"class": "btn btn-primary btn-block"}
        )  
    
    # since usernames are unique, check if it already exists
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError(('Please use a different username.'))
    
    # similar for emails
    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError(('Please use a different email address.'))

# login form - this only requires a valid username and email
# and provides an option to save your login for multiple sessions
class LoginForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[DataRequired()],
        # render-kw uses styles.css to determine the look of each element
        render_kw={"class": "input", "placeholder": "Username"} 
        )
    
    password = PasswordField(
        'Password', 
        validators=[DataRequired()],
        render_kw={"class": "input", "placeholder": "Password"}
        )
    
    remember_me = BooleanField(
        'Remember Me'
        )
    
    submit = SubmitField(
        'Log In',
        render_kw={"class": "btn btn-primary btn-block"}
        )
    
# request reset password form
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()],
    render_kw={"class": "input", "placeholder": "E-mail"})

    submit = SubmitField('Request Password Reset',
    render_kw={"class": "btn btn-primary btn-block"}
    )

# reset password form
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()],
    render_kw={"class": "input", "placeholder": "Password"}
    )
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')],
        render_kw={"class": "input", "placeholder": "Repeat Password"}
    )
    submit = SubmitField('Request Password Reset',
    render_kw={"class": "btn btn-primary btn-block"}
    )