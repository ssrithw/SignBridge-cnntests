from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes # at the bottom to avoid circular dependencies