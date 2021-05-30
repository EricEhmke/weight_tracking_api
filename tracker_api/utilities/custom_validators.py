import datetime
from marshmallow import ValidationError


def validate_date(date):
    try:
        dt_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        datetime.datetime.strftime(dt_obj, '%Y-%m-%d')
    except:
        raise ValidationError("Date validation error, ensure date is in 'YYYY-MM-DD' format")
