from tracker_api.models import User, Weight
from . import ma
from marshmallow import fields


class UserSchema(ma.SQLAlchemySchema):
    
    class Meta:
        model = User
    
    public_id = ma.auto_field(required=False)
    username = ma.auto_field()
    password = ma.auto_field()
    weights = ma.auto_field()


class WeightSchema(ma.SQLAlchemySchema):
    
    class Meta:
        model = Weight
        
    weight = ma.auto_field()
    date = fields.Date(format="%Y-%m-%d")
    id = ma.auto_field()
    public_id = ma.auto_field(required=False)  # setting required to false so an input can be validated with this field missing


user_schema = UserSchema(load_only=['password'], unknown='EXCLUDE')  # excludes the password when dumping
weight_schema = WeightSchema(load_only=['id'])
weights_schema = WeightSchema(many=True, load_only=['id'])
