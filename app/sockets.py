'''
sockets.py

Created by Nuha Rilwan
Last modified: 11/04/2026

socketio/webrtc stuff idk write a better description
'''

import sqlalchemy as sa
from flask import request
from flask_socketio import emit, join_room
from app import db, socketio
from app.models import Room

rooms = {}  # room_code -> [sid, sid]

# need to generate a code and send it back before anyone can join
def _get_room(code: str) -> Room | None:
    return db.session.scalar(
        sa.select(Room).where(Room.room_code == code)
    )

@socketio.on('join_room')
def on_join(data):
    code = data.get('room', '').strip().upper()

    # reject codes that don't exist in the database
    if not _get_room(code):
        emit('error', {'message': 'Invalid room code.'})
        return

    join_room(code)
    rooms.setdefault(code, [])

    if request.sid not in rooms[code]:
        rooms[code].append(request.sid)

    members = rooms[code]

    if len(members) == 2:
        emit('role', {'role': 'caller'}, to=members[0])
        emit('role', {'role': 'callee'}, to=members[1])
        emit('peer_ready', {}, to=code)
    elif len(members) > 2:
        # when room is full, reject the late joiner
        rooms[code].remove(request.sid)
        emit('error', {'message': 'Room is full.'})

@socketio.on('signal')
def on_signal(data):
    code = data.get('room', '').strip().upper()
    if code in rooms:
        emit('signal', data, to=code, include_self=False)

@socketio.on('disconnect')
def on_disconnect():
    for code, members in list(rooms.items()):
        if request.sid in members:
            members.remove(request.sid)
            emit('peer_left', {}, to=code)
            if not members:
                del rooms[code]   # clean up empty rooms
            break