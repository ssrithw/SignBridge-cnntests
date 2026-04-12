'''
services.py

Created by Shivangi Sritharan
Last modified: 11/04/2026

Contains various helpers and utilities.
'''

import random
import string
import sqlalchemy as sa
from app import db
from app.models import Room

# helper to generate room codes
def generate_room_code():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    numbers = ''.join(random.choices(string.digits, k=4))
    return f"{letters}-{numbers}"

# helper to check its uniqueness
def generate_unique_room_code():
    while True:
        code = generate_room_code()
        exists = db.session.scalar(
            sa.select(Room).where(Room.room_code == code)
        )
        if not exists:
            return code