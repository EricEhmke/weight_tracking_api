"""Flask configuration variables."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config:
    """Set Flask configuration from .env file."""

    # General Config
    SECRET_KEY = environ.get('SECRET_KEY')
    # SECRET_KEY = 'sercret'
    FLASK_APP = 'wsgi.py'
    FLASK_ENV = environ.get('FLASK_ENV')

    # Database
    MONGODB_DB_URL = environ.get('MONGO_DB_URL')
