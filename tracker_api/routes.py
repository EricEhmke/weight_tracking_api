from flask import request
from datetime import datetime as dt
from flask import current_app as app
from .models import db, User, Weight
from .schemas import user_schema, weight_schema, weights_schema, WeightSchema
from marshmallow import ValidationError
from functools import wraps
from .utilities.custom_validators import validate_date
from .utilities.db_services import create_weight_record, get_single_weight, get_all_weights
import jwt
import uuid
import datetime
import pandas as pd


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
        try:
            validate_date(date)
        except ValidationError as e:
            return {"message": {e.messages}}, 422
        weight_record = get_single_weight(current_user, date)
        if weight_record is None:
            return {"message": f"No record for {date} found"}, 404
        weight_json = weights_schema.dump(weight_record)
        return {"message": "Weight returned", "weight": weight_json}
    all_weights = get_all_weights(current_user)
    all_weights_json = weights_schema.dump(all_weights)
    return {"message": "All weights returned", "weights": all_weights_json}


@app.route('/api/v1/track/<string:date>', methods=['DELETE'])
@token_required
def delete_weight(current_user, date):
    try:
        validate_date(date)
    except ValidationError as err:
        return err.messages, 422
    weight_record = Weight.query.filter_by(user_id=current_user.id, date=date)
    if weight_record is not None:
        # delete all records in case there is a duplicate for that date
        for record in weight_record:
            db.session.delete(record)
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
        new_weight = create_weight_record(weight=data['weight'], date=data['date'], user_id=current_user_obj.id)
        new_weight_json = weight_schema.dump(new_weight)
        return {'message': 'Weight added', 'weight': new_weight_json}, 201


@app.route('/api/v1/track/average/<int:days>')
@app.route('/api/v1/track/average')
@token_required
def compute_avg(current_user, days=7):
    """
    Computes the rolling # `days` average weight. Missing dates are forward filled
    :param current_user: current_user information
    :param days: number of days to compute rolling average
    :return: the rolling average weights
    """
    all_weights_record = get_all_weights(current_user)
    all_weights = weights_schema.dump(all_weights_record)
    all_weights_df = pd.json_normalize(all_weights)
    # TODO: ffill any missing days between beginning and now
    # date_index = pd.date_range(first_date, last_date, freq='D')
    # all_weights_df.reindex(date_index, method='ffill')
    # https://pandas.pydata.org/pandas-docs/dev/reference/api/pandas.DataFrame.reindex.html

    weight_rolling_avg = all_weights.rolling(window=days).mean()
    # TODO: Add more weight records to get a rolling average
    return {'message': f'Rolling average for {days} days', 'weights': weight_rolling_avg.to_json()}