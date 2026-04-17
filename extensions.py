'''
extensions.py

Created by Shivangi Sritharan
Last modified: 13/04/2026

This file is used to initialize extensions to the application.
It exists to solve the problem of circular dependencies when
importing certain modules (e.g. socketio, database) directly
from the app.
'''

from flask_sqlalchemy import SQLAlchemy # for database
from flask_migrate import Migrate # for database migrations
from flask_login import LoginManager # for logins
from flask_wtf import CSRFProtect # to protect against csrf attacks
from flask_mail import Mail # to manage email sending
from flask_moment import Moment # for time stamps
from flask_limiter import Limiter # for rate limiting
from flask_limiter.util import get_remote_address # for rate limiting
from flask_socketio import SocketIO # for websocket access
from flask_bcrypt import Bcrypt # for password hashing

# initialize all modules
db = SQLAlchemy() # db represents the database object
migrate = Migrate() # migrate represents the migration engine
login = LoginManager()
csrf = CSRFProtect()
mail = Mail()
moment = Moment() 
socketio = SocketIO()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    # storage_uri has been moved to config.py
)
bcrypt = Bcrypt()

login.login_view = 'auth.login'
login.login_message = ('Please log in to access this page.')