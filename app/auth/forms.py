'''
forms.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains forms. Idk. Update later.
'''

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import Email, EqualTo, DataRequired  
from flask_login import current_user
from app.core.validators import password_complexity, unique_email, unique_username

# signup form

'''
# Validating password input server-side
Password must include:
At least 6 characters
At least one uppercase letter (A-Z)
At least one lowercase letter (a-z)
At least one number (0-9)
At least one special character (!@#$%^&*)
'''
class SignupForm(FlaskForm):
    email = StringField(
        validators=[DataRequired(), Email(), unique_email()],
        render_kw={"class": "input", "placeholder": "E-mail"}
    )

    username = StringField(
        'Username', 
        validators=[DataRequired(), unique_username()],
        render_kw={"class": "input", "placeholder": "Username"}
        )

    password = PasswordField(
        'Password', 
        validators=[DataRequired(), password_complexity],
        render_kw={"class": "input", "placeholder": "Password", "id" : "password"}
        )
    # repeat password
    repeat_password = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')],
        render_kw={"class": "input", "placeholder": "Repeat password"}
        )
    
    submit = SubmitField(
        'Sign Up',
        render_kw={"class": "btn btn-primary btn-block"}
        )

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
    repeat_password = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')],
        render_kw={"class": "input", "placeholder": "Repeat Password"}
    )
    submit = SubmitField('Request Password Reset',
    render_kw={"class": "btn btn-primary btn-block"}
    )