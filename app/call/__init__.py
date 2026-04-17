from flask import Blueprint

call_bp = Blueprint('call', __name__)

from app.call import routes