from tracker_api.models import User, Weight
from . import ma


class UserSchema(ma.SQLAlchemySchema):
    
    class Meta:
        model = User
    
    public_id = ma.auto_field()
    username = ma.auto_field()
    password = ma.auto_field()
    weights = ma.auto_field()


class WeightSchema(ma.SQLAlchemySchema):
    
    class Meta:
        model = Weight
        
    weight = ma.auto_field()
    date = ma.auto_field()
    id = ma.auto_field


user_schema = UserSchema(load_only=['password'], unknown='EXCLUDE')  # excludes the password when dumping
weight_schema = WeightSchema()
weights_schema = WeightSchema(many=True)
