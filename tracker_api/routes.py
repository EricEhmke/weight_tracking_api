from flask import request
from datetime import datetime as dt
from flask import current_app as app
from .models import db, User, Weight
from .schemas import user_schema, weight_schema, weights_schema
from marshmallow import ValidationError
from functools import wraps
from .utilities.custom_validators import validate_date
from .utilities.db_services import create_weight_record
import jwt
import uuid
import datetime


@app.post('/api/v1/login')
def login():
    """
    Checks for authorization header info & sends token when auth information is correct
    :return: a JWT token w/ user's public_id and token expiration date
    """
    auth = request.authorization
    if not auth:
        return {"message": "No input data provided"}, 400
    username = auth.username
    password = auth.password
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        password_match = existing_user.check_password(password)
        if password_match:
            token = jwt.encode({'public_id': existing_user.public_id,
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=14)},
                               app.config['SECRET_KEY'])

            return {'token': token}

    return {"message": "Incorrect username or password"}


def token_required(f):
    """
    Checks for an auth token before executing f
    :param f: A function
    :return: The decorated function or err if an auth token is not found
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        """
        Checks for an auth token. If token is found the wrapped func is executed and provided with the token data
        :param args: args
        :param kwargs: kwargs
        :return: A call to the wrapped function w/ current user data passed as an arg
        """
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return {"message": "Token is missing, please authenticate"}, 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except Exception as e:
            return {"message": "Token is invalid"}, 401
        if not current_user:
            return {"message": "Token is invalid"}, 401
        return f(current_user=current_user, *args, **kwargs)

    return decorated


def get_request_json(f):
    """
    Checks for request data and returns err 400 if none exists
    :param f: A function
    :return: Decorated function or err if no request data is provided
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        """
        Checks for request data
        :param args: args
        :param kwargs: kwargs
        :return: A call to the wrapped function with request data in JSON format
        """
        request_json = request.get_json(force=True)
        if not request_json:
            return {"message": "No input data provided"}, 401
        return f(request_json=request_json, *args, **kwargs)
    return decorated


@app.route('/api/v1/register', methods=['POST'])
@get_request_json
def register(request_json):
    """
    Registers a new user if their username is not already token
    :param request_json: request payload json
    :return: New user information
    """
    try:
        data = user_schema.load(data=request_json)
    except ValidationError as err:
        return err.messages, 422
    username = data['username']
    password = data['password']
    existing_user = User.query.filter_by(username=username).first()
    if not existing_user:
        user = User(public_id=str(uuid.uuid4()), username=username, created=dt.now())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        new_user = user_schema.dump(User.query.get(user.id))
        return {"message": "Registered new user", "user": new_user}
    return {"message": "Username already registered"}, 422


@app.route('/api/v1/track/<string:date>')
@app.route('/api/v1/track', methods=['GET'])
@token_required
def get_weights(current_user, date=None):
    """
    Returns weights for the current user
    :param current_user: current user information
    :param date: the date for which to return a weight - optional
    :return: A dict of weights
    """
    if date:
        return get_single_weight(current_user, date)
    return get_all_weights(current_user)


def get_single_weight(current_user, date):
    """
    Gets a single weight measurement for a date
    :param current_user: current user information
    :param date: date for which to return weight
    :return: a dict with a single weight measurement
    """
    weight = Weight.query.filter_by(user_id=current_user.id, date=date).first()
    if weight is None:
        return {"message": f"No record for {date} found"}, 404
    try:
        weight_json = weight_schema.dump(weight)
    except ValidationError as err:
        return err.messages, 422

    return {"message": "Weight returned", "weight": weight_json}


def get_all_weights(current_user):
    """
    Get all weights for the current user
    :param current_user: user details for the current user
    :return: All weights on record for current_user
    """
    weights = Weight.query.filter_by(user_id=current_user.id).all()
    weights_json = weights_schema.dump(weights)
    return {"message": "All weights returned", "weights": weights_json}


@app.route('/api/v1/track/<string:date>', methods=['DELETE'])
@token_required
def delete_weight(current_user, date):
    try:
        validate_date(date)
    except ValidationError as err:
        return err.messages, 422
    weight_record = Weight.query.filter_by(user_id=current_user.id, date=date).first()
    if weight_record is not None:
        db.session.delete(weight_record)
        db.session.commit()
    return {'message': 'Record deleted'}, 200


@app.route('/api/v1/track/<string:date>', methods=['POST', 'PUT'])
@token_required
@get_request_json
def add_or_update_weight(current_user, date, request_json):
    try:
        data = {
            "weight": request_json['weight'],
            "date": date
        }
        data = weight_schema.load(data=data, partial=True)
    except ValidationError as err:
        return err.messages, 422

    weight_record = Weight.query.filter_by(user_id=current_user.id, date=data['date']).first()
    if weight_record is not None:
        weight_record.weight = data['weight']
        db.session.commit()
        updated_weight = weight_schema.dump(Weight.query.get(weight_record.id))
        return {'message': 'Weight updated', 'weight': updated_weight}, 200
    else:
        current_user_obj = User.query.filter_by(public_id=current_user.public_id).first()
        print(f'data: {data} type: {type(data)}')
        new_weight = create_weight_record(weight=data['weight'], date=data['date'], user_id=current_user_obj.id)
        return {'message': 'Weight added', 'weight': new_weight}, 201
