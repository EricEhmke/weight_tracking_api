from flask import Flask
from pymongo import MongoClient
from flask_marshmallow import Marshmallow

ma = Marshmallow()


def init_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    client = MongoClient(app.config['MONGO_DB_URL'])
    db = client.weight_tracker

    ma.init_app(app)

    with app.app_context():
        from . import routes  # Import routes

        db.create_all()  # Create sql tables for our data models

        return app
