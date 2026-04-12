'''
routes.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains the routes every web page in this
application. It reuses code from the deprecated app.py but
is part of the new modularization effort.
'''

from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, current_app, abort
from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db, limiter
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm
from app.models import User, Room
from app.services import generate_unique_room_code

# check if user is logged in and has been online previously
@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

# route for landing page
@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Landing')

# route for about page
@bp.route('/about')
def about():
    return render_template('about.html', title='About Us')

# route for contact page
@bp.route('/contact')
def contact():
    return render_template('contact.html', title='Contact Us')

# route for joining a session
@bp.route("/join", methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def join():
    if request.method == 'POST':
        code = request.form.get('room_code', '').strip().upper()
        room = db.session.scalar(
            sa.select(Room).where(Room.room_code == code)
        )
        if not room:
            flash('Room not found. Check the code and try again.')
            return redirect(url_for('main.join'))
        return redirect(url_for('main.call', room=code))
    return render_template('join.html', title='Join A Session')

# route to create a new room and redirect to a waiting room
@bp.route("/create-room", methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def create_room():
    code = generate_unique_room_code()
    room = Room(room_code=code, owner_id=current_user.id)
    db.session.add(room)
    db.session.commit()          # only commits when user clicks "Finish" - change to either confirm or immediate
    return redirect(url_for('main.call', room=code))

# route for waiting page after starting a new chat
# DEPRECATED
'''
@bp.route("/waiting")
@limiter.limit("5 per minute")
def waiting():
    code = request.args.get('room', '').strip().upper()
    room = db.session.scalar(
        sa.select(Room).where(Room.room_code == code)
    )
    if not room:
        abort(404)
    return render_template("waiting.html", room_code=code, title='Waiting Room')
'''

# route for call page
@bp.route("/call")
@limiter.limit("10 per minute")
def call():
    code = request.args.get('room', '').strip().upper()
    room = db.session.scalar(
        sa.select(Room).where(Room.room_code == code)
    )
    if not room:
        abort(404)
    return render_template("call.html", room_code=code, title='Meeting Room')

# route for user profile page (updated)
@bp.route('/user/<username>') # this has a dynamic component that updates based on the user
@login_required # for obvious reasons
def user(username):
    # this SQLAlchemy function returns a user page if valid or 404 if invalid
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm() 
    return render_template('user.html', title='Your Account', user=user, form=form)

'''
# dummy for edit profile
@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
'''
# ------------- help pages -------------
# route for help page
@bp.route('/help')
def help():
    return render_template('help.html', title='Help')

# route for SLSL finger spelling chart
@bp.route('/slslchart')
def slslchart():
    return render_template('slslchart.html', title='SLSL Chart')

# route for video tutorial
@bp.route('/video_tutorial')
def video_tutorial():
    return render_template('video-tutorial.html', title='Video Tutorial')

# route for user guide
# not implemented yet!

