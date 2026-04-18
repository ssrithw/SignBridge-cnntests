'''
app/auth/email.py
Created by Shivangi Sritharan
Last modified 18/04/2026

This file contains a function that sends a password
reset email to a user. It is considered separate from 
the other email-related functions due to requiring tokens. 
'''
from flask import render_template, current_app
from app.core.email import send_email

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[SignBridge] Reset Your Password',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token)
            )

# The mail.send() method needs to access the configuration values 
# for the email server, and that can only be done by knowing what 
# the application context is