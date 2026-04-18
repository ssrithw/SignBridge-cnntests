'''
app/call/sockets.py

Created by Anuki Kithara
Last modified: 18/04/2026

Signaling and chat for call rooms.
'''

import sqlalchemy as sa
from flask import request
from flask_socketio import emit, join_room, leave_room
from extensions import db, socketio
from app.models import Room
from threading import Lock
from datetime import datetime, timezone

# ================= STATE =================
rooms       = {}     # room_code -> set of sids
sid_to_room = {}     # sid        -> room_code
room_lock   = Lock()

def _get_room(code: str):
    return db.session.scalar(
        sa.select(Room).where(Room.room_code == code)
    )


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ================= JOIN ROOM =================
@socketio.on('join_room')
def on_join(data):
    code = (data.get('room') or '').strip().upper()
    sid  = request.sid

    if not code:
        emit('error', {'message': 'Missing room code.'})
        return

    room = _get_room(code)
    if not room:
        emit('error', {'message': 'Invalid room code.'})
        return

    with room_lock:
        rooms.setdefault(code, set())
        if sid in rooms[code]:
            participants = len(rooms[code])     # idempotent re-join
        else:
            if len(rooms[code]) >= 2:
                emit('error', {'message': 'Room is full.'})
                return
            rooms[code].add(sid)
            sid_to_room[sid] = code
            participants = len(rooms[code])

    # join_room / emit acquire their own Flask-SocketIO locks — do these
    # OUTSIDE room_lock to avoid lock-ordering deadlocks.
    join_room(code)

    if participants == 1:
        emit('role', {'role': 'caller'})
    elif participants == 2:
        emit('role', {'role': 'callee'})
        emit('peer_ready', {}, to=code)
        emit(
            'chat_message',
            {'sender': 'system',
             'message': 'User joined the chat',
             'timestamp': _iso_utc_now()},
            to=code,
            include_self=False # joining user should not be able to see their own "user joined"
        )


# ================= SIGNALING =================
@socketio.on('signal')
def on_signal(data):
    code = (data.get('room') or '').strip().upper()
    sid  = request.sid

    # sender must actually be in the room they're signaling. prevents spoofing
    if sid_to_room.get(sid) != code:
        return
    if code not in rooms:
        return

    emit('signal', data, to=code, include_self=False)


# ================= DISCONNECT CLEANUP =================
@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid

    notify = False
    code   = None
    with room_lock:
        code = sid_to_room.pop(sid, None)
        if code and code in rooms:
            rooms[code].discard(sid)
            if not rooms[code]:
                rooms.pop(code, None)
            else:
                notify = True

    if not code:
        return

    try:
        leave_room(code)
    except Exception:
        pass

    if notify:
        emit('peer_left', {}, to=code)
        emit(
            'chat_message',
            {'sender': 'system',
             'message': 'User left the chat',
             'timestamp': _iso_utc_now()},
            to=code
        )


# ================= CHAT =================
@socketio.on('chat_message')
def on_chat_message(data):
    code    = (data.get('room') or '').strip().upper()
    message = (data.get('message') or '').strip()
    sid     = request.sid

    if not code or not message:
        return

    # Simple payload cap.
    if len(message) > 1000:
        message = message[:1000]

    # Anti-spoof (already present in original — keeping it).
    if sid_to_room.get(sid) != code:
        return

    emit(
        'chat_message',
        {'sender': 'peer',
         'message': message,
         'timestamp': _iso_utc_now()},
        to=code,
        include_self=False
    )
