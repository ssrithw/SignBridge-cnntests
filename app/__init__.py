from flask import Flask
from config import Config
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from app.errors.handlers import ratelimit_exceeded, page_not_found, internal_error
from extensions import db, migrate, login, csrf, mail, moment, limiter, socketio, bcrypt
import sqlalchemy as sa

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # extensions
    db.init_app(app) # database
    migrate.init_app(app, db) # db migration engine
    csrf.init_app(app) # protection against csrf attacks
    login.init_app(app) # login
    mail.init_app(app) #flask-mail for email operations
    moment.init_app(app) # flask-moment for timezone conversion
    limiter.init_app(app) # flask-limiter for rate limiting
    socketio.init_app(app, async_mode='gevent', cors_allowed_origins='*') 
    bcrypt.init_app(app)

    # register blueprints here
    # auth blueprint
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    # errors blueprint
    from app.errors import errors_bp
    app.register_blueprint(errors_bp, url_prefix='/errors')

    # call blueprint
    from app.call import call_bp
    app.register_blueprint(call_bp)

    # help blueprint
    from app.help import help_bp
    app.register_blueprint(help_bp, url_prefix='/help')

    # main blueprint
    from app.main import main_bp
    app.register_blueprint(main_bp)

    # user blueprint
    from app.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/your-account')

    # call rate limit from limiter instead of using 
    # flask's built in limiter
    limiter._rate_limit_exceeded_handler = ratelimit_exceeded
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(429, ratelimit_exceeded)
    app.register_error_handler(500, internal_error)

    # register socket event handlers
    from app.call import sockets

    if not app.debug and not app.testing:
        import sqlalchemy as sa
        from app.models import User

        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])

            secure = () if app.config['MAIL_USE_TLS'] else None

            class DynamicSMTPHandler(SMTPHandler):
                def emit(self, record):
                    with app.app_context():
                        admins = db.session.scalars(
                            sa.select(User).where(User.is_admin == True)
                        ).all()
                        self.toaddrs = [u.email for u in admins if u.email]

                    if not self.toaddrs:
                        return

                    super().emit(record)

            mail_handler = DynamicSMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=[],
                subject='SignBridge Failure',
                credentials=auth,
                secure=secure
            )

            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        log_dir = os.path.join(app.root_path, 'logs')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'signbridge.log'),
            maxBytes=10240,
            backupCount=10
        )

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('SignBridge startup complete')

    from app import models

    return app