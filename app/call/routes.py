'''
app/call/routes.py
Created by Shivangi Sritharan
Last modified: 18/04/2026

This file contains the routes for call
room-related routes.
'''

from flask import current_app
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
import sqlalchemy as sa
from extensions import db, limiter
from app.models import Room
from app.call import call_bp
from app.call.services import generate_unique_room_code
from app.call.forms import JoinForm, CreateRoomForm

# route for joining a session
@call_bp.route('/join', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def join():
    form = JoinForm()
    if form.validate_on_submit():
        # codes are not case-sensitive
        code = form.room_code.data.strip().upper()
        current_app.logger.info(f"Room join attempt: code={code} ip={request.remote_addr}")
        room = db.session.scalar(
            sa.select(Room).where(Room.room_code == code)
        )
        if not room:
            current_app.logger.warning(f"Failed room join (not found): code={code} ip={request.remote_addr}")
            flash('Room not found. Check the code and try again.')
            return redirect(url_for('call.join'))
        return redirect(url_for('call.call', room=code))
    
    create_form = CreateRoomForm()

    return render_template('call/join.html', title='Join A Room', form=form, create_form=create_form)

# route to create a new room and redirect to a waiting room
@call_bp.route('/create-room', methods=['POST'])
@limiter.limit('5 per minute', methods=['POST'])
@login_required
def create_room():
    form = CreateRoomForm()

    if form.validate_on_submit():
        code = generate_unique_room_code()
        room = Room(room_code=code, owner_id=current_user.id)
        db.session.add(room)
        db.session.commit()
        current_app.logger.info(f"Room created: code={code} owner_id={current_user.id} ip={request.remote_addr}")
        return redirect(url_for('call.call', room=code))

    return redirect(url_for('call.join'))

# route for call page
@call_bp.route('/call')
@limiter.limit('10 per minute')
def call():
    # code is not case-sensitive
    code = request.args.get('room', '').strip().upper()
    current_app.logger.info(f"Call page access attempt: code={code} ip={request.remote_addr}")
    room = db.session.scalar(
        sa.select(Room).where(Room.room_code == code)
    )
    if not room:
        current_app.logger.warning(f"Invalid room access attempt: code={code} ip={request.remote_addr}")
        abort(404)
    current_app.logger.info(f"Room accessed: code={code} user_id={getattr(current_user, 'id', None)}")
    return render_template('call/call.html', room_code=code, title='Meeting Room')