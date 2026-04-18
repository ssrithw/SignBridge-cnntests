'''
app/call/forms.py
Created by Shivangi Sritharan
Last modified: 18/04/2026

This file contains the server-side code for 
forms related to the call room. The forms are 
implemented with Flask-WTForms.
'''

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class JoinForm(FlaskForm):
    user_name = StringField(
        "Your Name", 
        validators=[DataRequired()],
        # render_kw tells the application how to render the form with CSS
        render_kw={"class": "input", "placeholder": "Your Name"}
    )
    room_code = StringField(
        "Room Code", 
        validators=[DataRequired()],
        render_kw={"class": "input", "placeholder": "Room Code"}
    )

    submit = SubmitField(
        "Start Call",
        render_kw={"class": "btn btn-primary btn-block"}
    )

# this is a simple submit-only form because current logic requires
# users to be signed in to create a room.
class CreateRoomForm(FlaskForm):
    submit = SubmitField(
        "Create New Session",
        render_kw={"class": "btn btn-secondary btn-block"}
    )