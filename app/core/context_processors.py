from flask_login import current_user
from flask import request
from app.core.nav import NAV_MAP

def inject_globals():
    active = request.endpoint

    return {
        "current_user": current_user,
        "is_authenticated": current_user.is_authenticated,
        "active_endpoint": active,
        "active_nav": NAV_MAP.get(active, "")
    }