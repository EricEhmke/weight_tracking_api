from tracker_api.models import db, User, Weight
import uuid


def create_weight_record(weight, date, user_id, public_id=None):
    """
    Creates a new weight record and returns an id
    :param weight: str or int
    :param date: datetime date
    :param user_id: current user id
    :param public_id: a uuid
    :return:
    """
    if public_id is None:
        public_id = str(uuid.uuid4())
    weight_record = Weight(weight=weight, date=date, user_id=user_id, public_id=public_id)
    db.session.add(weight_record)
    db.session.commit()
    new_weight = Weight.query.filter_by(user_id=user_id, date=date).first()
    return new_weight


def get_single_weight(current_user, date):
    """
    Gets a single weight measurement for a date
    :param current_user: current user information
    :param date: date for which to return weight
    :return: a dict with a single weight measurement
    """
    weight = Weight.query.filter_by(user_id=current_user.id, date=date).first()
    return weight


def get_all_weights(current_user):
    """
    Get all weights for the current user
    :param current_user: user details for the current user
    :return: All weights on record for current_user
    """
    return Weight.query.filter_by(user_id=current_user.id).all()
