'''
config.py
Created by Shivangi Sritharan
Last modified: 10/04/2026

This file contains configuration stuff.
'''

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env')) # set variables before class is constructed

class Config:
    # secret key for token generation
    # todo: add a real secret key lol
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # the flask-SQLAlchemy extension takes the location of the application's 
    # database from the SQLALCHEMY_DATABASE_URI configuration variable
    # if the url isn't defined in DATABASE_URL it will fall back to
    # app.db found locally.
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    #SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://signbridge:thesbdatabase123@localhost:5432/signbridgedb'

    uri = os.environ.get("DATABASE_URL")

    if not uri:
        raise RuntimeError("DATABASE_URL is not set. Application will not start.")

    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+psycopg2://", 1)

    SQLALCHEMY_DATABASE_URI = uri

    # the flask-limiter extension stores data in this
    # because limiter uses the limit library this is kept separate from sqlalchemy
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI')
    
    # admin email mailing list lol
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']