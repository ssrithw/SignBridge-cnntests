from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_moment import Moment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.errors.handlers import ratelimit_exceeded

# socketio for webrtc
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, async_mode="gevent", cors_allowed_origins="*")
db = SQLAlchemy() # db represents the database object
migrate = Migrate() # migrate represents the migration engine
login = LoginManager() # session auth stuff
login.login_view = 'auth.login'
login.login_message = ('Please log in to access this page.')
mail = Mail()
moment = Moment() 
socketio = SocketIO() # for webrtc

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    # storage_uri has been moved to config.py
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # extensions
    db.init_app(app) # database
    migrate.init_app(app, db)
    login.init_app(app) # login
    mail.init_app(app) #flask-mail for email operations
    moment.init_app(app) # flask-moment for timezone conversion
    limiter.init_app(app) # flask-limiter for rate limiting
    socketio.init_app(app, async_mode='gevent', cors_allowed_origins='*') 

    limiter._rate_limit_exceeded_handler = ratelimit_exceeded

    # register the blueprints with the application
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # register socket event handlers
    from app import sockets

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='SignBridge Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/signbridge.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('SignBridge startup')

    return app

from app import models