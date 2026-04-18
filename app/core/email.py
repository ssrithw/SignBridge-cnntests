'''
app/core/email.py
Created by Shivangi Sritharan
Last modified 18/04/2026

This file contains functions related to
emailing users. These functions are reused
across all blueprints that use emails.
'''
from threading import Thread # for async mail sending
from flask import render_template, current_app
from flask_mail import Message
from extensions import mail
    
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

# The mail.send() method needs to access the configuration values 
# for the email server, and that can only be done by knowing what 
# the application context is