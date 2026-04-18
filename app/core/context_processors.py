'''
app/core/context_processors.py

Created by Shivangi Sritharan
Last modified: 18/04/2026

This file contains context processors used across
the application.
'''

from flask_login import current_user
from flask import request
from app.core.nav import NAV_MAP

# inject globals into base.html
def inject_globals():
    active = request.endpoint

    return {
        "current_user": current_user,
        "is_authenticated": current_user.is_authenticated,
        "active_endpoint": active,
        "active_nav": NAV_MAP.get(active, "")
    }