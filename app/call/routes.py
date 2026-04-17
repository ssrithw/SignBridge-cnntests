'''
call/routes.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains the routes every web page in this
application. It reuses code from the deprecated app.py but
is part of the new modularization effort.
'''

from flask import current_app
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
import sqlalchemy as sa
from extensions import db, limiter
from app.models import Room
from app.call import call_bp
from app.call.services import generate_unique_room_code

# route for joining a session
@call_bp.route('/join', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def join():
    if request.method == 'POST':
        code = request.form.get('room_code', '').strip().upper() # codes are case-insensitive
        current_app.logger.info(f"Room join attempt: code={code} ip={request.remote_addr}")
        room = db.session.scalar(
            sa.select(Room).where(Room.room_code == code)
        )
        if not room:
            current_app.logger.warning(f"Failed room join (not found): code={code} ip={request.remote_addr}")
            flash('Room not found. Check the code and try again.')
            return redirect(url_for('call.join'))
        return redirect(url_for('call.call', room=code))
    return render_template('call/join.html', title='Join A Room')

# route to create a new room and redirect to a waiting room
@call_bp.route('/create-room', methods=['POST'])
@limiter.limit('5 per minute')
@login_required
def create_room():
    code = generate_unique_room_code()
    room = Room(room_code=code, owner_id=current_user.id)
    db.session.add(room)
    db.session.commit()
    current_app.logger.info(f"Room created: code={code} owner_id={current_user.id} ip={request.remote_addr}")
    return redirect(url_for('call.call', room=code))

# route for call page
@call_bp.route('/call')
@limiter.limit('10 per minute')
def call():
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