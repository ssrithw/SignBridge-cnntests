from flask import Blueprint

help_bp = Blueprint('help', __name__)

from app.help import routes