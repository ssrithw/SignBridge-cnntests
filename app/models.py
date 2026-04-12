'''
models.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

database description
'''

from datetime import datetime, timezone
from typing import Optional # to let values be a specific type or None (for nullable fields)
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # this helper implements methods required by flask-login's session mgmt system
from hashlib import md5
from time import time
import jwt

# flask-login expects that the application will configure a user loader function that can be called to load a user given the ID
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class User(UserMixin, db.Model):
    # id is unique and also the primary key
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    # UNIQUE=TRUE (since users login with username)
    username: so.Mapped[str] = so.mapped_column(sa.String(50), index=True, unique=True, nullable=False)

    # email is email 
    email: so.Mapped[str] = so.mapped_column(sa.String(100), index=True, unique=True, nullable=False)

    # we store password hashes instead of raw passwords for security reasons. dulitha or dulneth please explain
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), nullable=False)

    # last seen isnt necessary but is nice
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    # orm relationships for better querying
    rooms = db.relationship(
        "Room",
        back_populates="owner" # rooms.owner shows the owner of a room
    )
    rooms_joined = db.relationship(
        "Room",
        secondary="room_participant",
        back_populates="participants" # user.rooms_joined shows the rooms a user is in
    )
    messages = db.relationship(
        "Message", back_populates="user" # user.messages shows a user's messages
    )

    # repr tells python how to print the table.
    # this is used for debugging
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    # we use werkzeug for password hashing and checking
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # add profile pictures with Gravatar
    def avatar(self, size):
        # convert email to lowercase (required by gravatar) and encode 
        # the string as bytes so python can work with it (see https://docs.gravatar.com/avatars/python/)
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    # reset password token
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    # invokable from the class itself
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)

class Room(db.Model):
    # room_id
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    # room code (different!)
    room_code: so.Mapped[str] = so.mapped_column(sa.String(9), index=True, unique=True, nullable=False)
    # room created at (timezone currently UTC but may need to be changed)
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc), nullable=False)
    # owner id - foreign key from the user table
    owner_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True, nullable=False)

    # orm relationships
    owner = db.relationship(
        "User",
        back_populates="rooms" # user.rooms shows all rooms owned by a user
    )
    participants = db.relationship(
        "User",
        secondary="room_participant",
        back_populates="rooms_joined" # room.participants shows the users in room
    )
    messages = db.relationship(
        "Message", back_populates="room" # room.messages shows the messages in a room
    )
    transcripts = db.relationship(
        "Transcript", back_populates="room" # room.transcripts shows the transcripts in a room
    )

    # no real need to speed up querying for values in this table so no orm relationships

    def __repr__(self):
        return '<Room {}>'.format(self.id)

# users to rooms is a many to many relationship so this table exists to break it up
class RoomParticipant(db.Model):
    # id
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    # user id 
    rp_user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True, nullable=False)
    # room id
    rp_room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Room.id), index=True, nullable=False)

    def __repr__(self):
        return '<RoomParticipant {}>'.format(self.id)

# transcript generated by model
# can be started, stopped (ie a session can have multiple), can be downloaded
class Transcript(db.Model):
    # id
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    # content of transcript. this does not need to be unique and the table doesn't need to be indexed on it (storage issues)
    ts_content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    # creation
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc), nullable=False)
    # foreign key room id
    room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Room.id), index=True, nullable=False)

    # orm relationships
    room = db.relationship(
        "Room", back_populates="transcripts" # transcript.room is sort of pointless but shows which room a transcript is from
    )

    def __repr__(self):
        return '<Transcript {}>'.format(self.ts_content)

# messages in the chat
class Message(db.Model):
    # id
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    # content
    msg_content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    # creation
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc), nullable=False)
    # user id 
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True, nullable=False)
    # room id
    room_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Room.id), index=True, nullable=False)

    # orm relationships
    room = db.relationship(
        "Room", back_populates="messages" # message.room shows the room a message was sent in
    )
    
    user = db.relationship(
        "User", back_populates="messages" # message.user shows the owner of a message
    )

    def __repr__(self):
        return '<Message {}>'.format(self.msg_content)