from flask_pymongo import PyMongo
from dateutil.parser import isoparse, parse
from datetime import timedelta, timezone, datetime
import shortuuid

mongo = PyMongo()


def get_all_user():
    """
    Get all users
    :return: list
    """
    return list(mongo.db.users.find())


def get_user(email):
    """
    Get one user by email
    :param email:
    :return: dict
    """
    return next(iter(mongo.db.users.find({'email': email})), None)


def upsert_user(email, display_name):
    """
    Upsert user
    :param email:
    :param display_name:
    :return: pymongo.results
    """
    user = {'$set': {'email': email, 'display_name': display_name}}
    result = mongo.db.users.update_one({'email': email}, user, upsert=True)
    return result


def delete_user(email):
    return mongo.db.users.delete_one({'email': email})


def delete_users(emails):
    query = {'email': {'$in': emails}}
    return mongo.db.users.delete_many(query)


def update_rotation(email, is_duty, seq):
    return mongo.db.users.update_one({'email': email}, {'$set': {'is_duty': is_duty, 'seq': seq}})


def move_next():
    """
    Increment seq of on-duty users
    :return: All users
    """
    users = list(mongo.db.users.find())
    max_seq = max(u.get('seq', -1) for u in users)
    if max_seq >= 0:
        on_duty_users = [u for u in users if u.get('seq', -1) >= 0 and u.get('is_duty', False)]
        for u in on_duty_users:
            if u['seq'] == max_seq:
                mongo.db.users.update_one({'_id': u['_id']}, {'$set': {'seq': 0}})
            else:
                mongo.db.users.update_one({'_id': u['_id']}, {'$set': {'seq': u['seq'] + 1}})

    return mongo.db.users.find()


def get_current_user():
    return mongo.db.users.find_one({'is_current': True})


def upasert_holiday(date, remarks):
    utc_diff = datetime.utcnow() - datetime.now()
    utc = isoparse(date) + utc_diff
    return mongo.db.holidays.update_one(
        {'date': utc},
        {
            '$set': {
                'date': utc,
                'remarks': remarks,
                'holiday_id': shortuuid.random(6)
            }
        },
        upsert=True
    )


def get_holidays():
    data = mongo.db.holidays.find().sort('date')
    utc_diff = datetime.utcnow() - datetime.now()
    result = []
    for d in data:
        result.append({
            'holiday_id': d.get('holiday_id'),
            'date': d.get('date') - utc_diff,
            'remarks': d.get('remarks')
        })

    return result


def delete_holiday(holiday_id):
    return mongo.db.holidays.delete_one({'holiday_id': holiday_id})


def add_vacation(email, start_date, end_date, remarks):
    start_date = parse(start_date)
    end_date = parse(end_date)
    vacation_hash = _get_vacation_hash(email, start_date, end_date)

    # Check existing vacation
    vacation = get_vacation_by_hash(vacation_hash)

    if vacation is None:
        utf_start_date = _get_utf_midnight(start_date)
        utf_end_date = _get_utf_midnight(end_date)
        return mongo.db.users.update_one(
            {'email': email},
            {'$push': {
                'vacations': {
                    'hash': vacation_hash,
                    'start_date': utf_start_date,
                    'end_date': utf_end_date,
                    'remarks': remarks
                }
            }}
        )
    else:
        raise KeyError


def get_vacation_by_hash(vacation_hash):
    return mongo.db.users.find_one(
        {'vacations.hash': vacation_hash}
    )


def _get_utf_midnight(date):
    utc_diff = datetime.utcnow() - datetime.now()
    result = date + utc_diff
    return result

def _get_vacation_hash(email, start_date, end_date):
    """
    Create hash for vacation
    :param email: email
    :param start_date: datetime
    :param end_date: datetime
    :return: hash
    """
    hash_key = (email, start_date, end_date)
    return hash(hash_key)

