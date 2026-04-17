'''
app/call/sockets.py

Created by Nuha Rilwan
Last modified: 11/04/2026

socketio/webrtc stuff idk write a better description
'''
'''
import sqlalchemy as sa
from flask import request
from flask_socketio import emit, join_room, leave_room
from extensions import db, socketio
from app.models import Room

rooms = {}  # room_code uses set(sid, sid)

# need to generate a code and send it back before anyone can join
def _get_room(code: str):
    return db.session.scalar(
        sa.select(Room).where(Room.room_code == code)
    )

@socketio.on('join_room')
def on_join(data):
    code = (data.get('room') or '').strip().upper()
    sid = request.sid

    room = _get_room(code)

    # reject codes that don't exist in the database
    if not room:
        emit('error', {'message': 'Invalid room code.'})
        return

    # join socket.io room
    join_room(code)

    # get current room participants using Socket.IO internal state
    participants = list(socketio.server.manager.get_participants('/', code))

    # prevent duplicates
    rooms[code].add(sid)

    # enforce max 2 participants
    if len(participants) > 2:
        leave_room(code)
        emit('error', {'message': 'Room is full.'})
        return

    # assign roles deterministically
    if len(participants) == 1:
        emit('role', {'role': 'caller'})

    elif len(participants) == 2:
        emit('role', {'role': 'callee'})
        emit('peer_ready', {}, to=code)

@socketio.on('signal')
def on_signal(data):
    code = (data.get('room') or '').strip().upper()
    if code in rooms:
        emit('signal', data, to=code, include_self=False)

@socketio.on('disconnect')
def on_disconnect():
    # socketio handles this automatically so the only
    # real change here is to emit a message to the remaining
    # participant
    emit('peer_left', {}, broadcast=True)
'''

import sqlalchemy as sa
from flask import request
from flask_socketio import emit, join_room, leave_room
from extensions import db, socketio
from app.models import Room
from threading import Lock
from datetime import datetime

# ================= STATE =================
rooms = {}
sid_to_room = {}
room_lock = Lock()


def _get_room(code: str):
    return db.session.scalar(
        sa.select(Room).where(Room.room_code == code)
    )


# ================= JOIN ROOM =================
@socketio.on('join_room')
def on_join(data):
    code = (data.get('room') or '').strip().upper()
    sid = request.sid

    room = _get_room(code)
    if not room:
        emit('error', {'message': 'Invalid room code.'})
        return

    with room_lock:
        rooms.setdefault(code, set())
        if len(rooms[code]) >= 2:
            emit('error', {'message': 'Room is full.'})
            return
        rooms[code].add(sid)
        sid_to_room[sid] = code
        participants = len(rooms[code])

    # BUG FIX 4: join_room() is called OUTSIDE room_lock.
    # In threading mode Flask-SocketIO acquires its own internal locks inside
    # join_room/leave_room. Calling them while holding room_lock risks deadlock
    # if those internal locks and room_lock are ever acquired in the opposite
    # order on another greenlet/thread.
    join_room(code)

    if participants == 1:
        emit('role', {'role': 'caller'})
    elif participants == 2:
        emit('role', {'role': 'callee'})
        emit('peer_ready', {}, to=code)
        emit('chat_message', {'message': 'User joined the chat'}, to=code)


# ================= SIGNALING =================
@socketio.on('signal')
def on_signal(data):
    code = (data.get('room') or '').strip().upper()
    if code in rooms:
        emit('signal', data, to=code, include_self=False)


# ================= DISCONNECT CLEANUP =================
@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    code = sid_to_room.pop(sid, None)
    if not code:
        return

    # BUG FIX 5: Determine what needs to happen while holding the lock, but
    # call leave_room() and emit() only after releasing it (same deadlock
    # risk as join_room above).
    notify = False
    with room_lock:
        if code in rooms:
            rooms[code].discard(sid)
            if not rooms[code]:
                rooms.pop(code, None)
            else:
                notify = True

    # Always leave the SocketIO room, regardless of whether anyone remains.
    leave_room(code)

    if notify:
        emit('peer_left', {}, to=code)
        emit('chat_message', {'message': 'User left the chat'}, to=code)

# ================= CHAT =================
@socketio.on('chat_message')
def on_chat_message(data):
    code = (data.get('room') or '').strip().upper()
    message = (data.get('message') or '').strip()
    sid = request.sid

    # basic validation
    if not code or not message:
        return

    # ensure sender is actually in the room (prevents spoofing)
    if sid_to_room.get(sid) != code:
        return

    # broadcast to the other peer
    emit('chat_message', {
    'message': message,
    'timestamp': datetime.utcnow().isoformat()
}, to=code, include_self=False)
