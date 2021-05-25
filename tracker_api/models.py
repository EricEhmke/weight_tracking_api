"""Data models."""
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime


class User(db.Model, UserMixin):
    """Data model for user accounts."""

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    username = db.Column(
        db.String(64),
        index=False,
        unique=True,
        nullable=False
    )
    public_id = db.Column(
        db.String(64),
        unique=True
    )
    password = db.Column(
        db.String(200),
        nullable=False,
        unique=False,
        primary_key=False
    )
    weights = db.relationship(
        'Weight',
        backref='user',
        lazy=True,
        cascade="all, delete-orphan"
    )
    created = db.Column(
        db.DateTime,
        index=False,
        unique=False,
        nullable=False,
        default=datetime.datetime.utcnow()
    )
    admin = db.Column(
        db.Boolean,
        index=False,
        unique=False,
        nullable=False,
        default=False
    )
    
    def set_password(self, password):
        self.password = generate_password_hash(password, method='sha256')
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Weight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    def __repr__(self):
        return f'{self.date} - {self.weight}'
