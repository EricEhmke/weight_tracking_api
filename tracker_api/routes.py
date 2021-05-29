from flask import request, render_template, make_response, jsonify
from datetime import datetime as dt
from flask import current_app as app
from .models import db, User, Weight
from .schemas import user_schema, weight_schema, weights_schema, UserSchema
from marshmallow import ValidationError
from functools import wraps
import jwt
import uuid
import datetime


@app.route('/', methods=['GET'])
def index():
    return 'Hello'


@app.post('/api/v1/login')
def login():
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
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return {"message": "Token is missing"}, 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except Exception as e:
            print(e)
            return {"message": "Token is invalid"}, 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.post('/api/v1/register')
def register():
    request_json = request.get_json()
    if not request_json:
        return {"message": "No input data provided"}, 400
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
    if date:
        print(f'date: {date}')
        date, err = validate_date(date)
        if err:
            print('error in validation')
            print(err.messages)
            return err.messages, 422
        return get_single_weight(current_user, date)
    return get_all_weights(current_user)


def validate_date(date):
    try:
        dt_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        dt_obj = datetime.datetime.strftime(dt_obj, '%Y-%m-%d')
        return dt_obj, None
    except Exception:
        return None, ValidationError("Date validation error, ensure date is in 'YYYY-MM-DD' format")


def get_single_weight(current_user, date):
    weight = Weight.query.filter_by(user_id=current_user.id, date=date).first()
    if weight is None:
        return {"message": f"No record for {date} found"}, 200
    weight_json = weight_schema.dump(weight)
    return {"message": "Weight returned", "weight": weight_json}


def get_all_weights(current_user):
    weights = Weight.query.filter_by(user_id=current_user.id).all()
    weights_json = weights_schema.dump(weights)
    return {"message": "All weights returned", "weights": weights_json}


@app.route('/api/v1/track', methods=['POST'])
@token_required
def add_weight(current_user):
    request_json = request.get_json()
    if not request_json:
        return {'message': 'No input data provided'}, 400
    try:
        # This may be able to be refactored out and use the date validation function above
        data = weight_schema.load(data=request_json)
    except ValidationError as err:
        return err.messages, 422

    weight = data['weight']
    date = data['date']
    current_user_obj = User.query.filter_by(public_id=current_user.public_id).first()
    new_weight = Weight(weight=weight, date=date, user_id=current_user_obj.id, public_id=str(uuid.uuid4()))
    print(f'new weight: {new_weight}')
    db.session.add(new_weight)
    db.session.commit()
    new_weight = weight_schema.dump(Weight.query.get(new_weight.id))
    return {'message': 'Weight added', 'weight': new_weight}


@app.route('/api/v1/track', methods=['DELETE'])
@token_required
def delete_weight(current_user):
    pass


@app.route('/api/v1/track', methods=['PUT'])
@token_required
def update_weight(current_user):
    pass
