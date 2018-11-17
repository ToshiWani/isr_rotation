from flask import current_app
from flask_pymongo import PyMongo
from dateutil.parser import isoparse, parse
from datetime import timedelta, timezone, datetime
import shortuuid
from typing import Optional

mongo = PyMongo()


def get_all_user():
    """
    Get all users
    :return: list
    """
    return list(mongo.db.users.find())


def get_all_on_duty_user():
    _sync_all_vacation()
    return list(mongo.db.users.find({'is_duty': {'$eq': True}}))


def get_all_off_duty_user():
    return list(mongo.db.users.find({'is_duty': {'$eq': False}}))


def count_on_duty_users() -> int:
    return mongo.db.users.find({'is_duty': {'$eq': True}}).count()


def get_user(email: str) -> Optional[dict]:
    """
    Get one user by email
    :param email:
    :return: dict
    """
    return next(iter(mongo.db.users.find({'email': email})), None)


def get_user_by_seq(seq: int) -> Optional[dict]:
    return next(iter(mongo.db.users.find({'seq': seq})), None)


def is_everyone_on_vacation() -> bool:
    """
    Check if all on-duty users are on vacation
    :return:
    """
    users = get_all_on_duty_user()
    result = True
    for u in users:
        is_vacation = u.get('is_vacation')
        if not is_vacation:
            result = False
            break
    return result


def add_user(email: str, display_name: str):
    """
    Add user
    :param email:
    :param display_name:
    :return: pymongo.results
    """
    return mongo.db.users.insert(
        {
            'email': email,
            'display_name': display_name,
            'is_duty': False,
            'seq': -1,
            'is_current': False,
            'vacations': [],
            'disp_seq': -1,
            'is_vacation': False
        }
    )


def update_user(email, display_name):
    """
    Update user
    :param email:
    :param display_name:
    :return: pymongo.results
    """
    user = {'$set': {'email': email, 'display_name': display_name}}
    result = mongo.db.users.update_one(
        {'email': email},
        user,
        upsert=False
    )
    return result


def delete_user(email):
    return mongo.db.users.delete_one({'email': email})


def delete_users(emails):
    query = {'email': {'$in': emails}}
    return mongo.db.users.delete_many(query)


def update_rotation(email, is_duty, seq):
    _sync_vacation(email)
    return mongo.db.users.update_one(
        {'email': email},
        {'$set': {'is_duty': is_duty, 'seq': seq, 'disp_seq': seq}}
    )


def get_current_rotation() -> int:
    result = 0
    rotation = mongo.db.rotation.find().sort('last_update', -1).limit(1)
    if rotation.count() == 0:
        mongo.db.rotation.insert_one({
            'current': 0,
            'last_update': datetime.utcnow()
        })
    else:
        result = rotation[0]['current']

    return result


def set_current_rotation(seq: int) -> None:
    rotation = mongo.db.rotation.find().sort('last_update', -1).limit(1)
    if rotation.count() == 0:
        mongo.db.rotation.insert_one({
            'current': seq,
            'last_update': datetime.utcnow()
        })
    else:
        mongo.db.rotation.update_one(
            {'_id': rotation[0]['_id']},
            {'$set': {'current': seq, 'last_update': datetime.utcnow()}}
        )

    pass


def get_next_rotation() -> int:
    # Get current rotation seq
    current_rotation = get_current_rotation()

    # Count current on-duty users
    on_duty_count = count_on_duty_users()

    # Return zero if current rotation exceed max. Otherwise increment it.
    return 0 if current_rotation >= on_duty_count - 1 else current_rotation + 1


def move_next() -> Optional[int]:
    """
    Increment seq of on-duty users
    :return: Current rotation
    """
    _sync_all_vacation()

    # Count current on-duty users
    on_duty_count = count_on_duty_users()

    # Exit out if no one is on-duty
    if on_duty_count < 1:
        return None

    # Exit out if all on-duty users are vacation
    if is_everyone_on_vacation():
        return None

    next_rotation = get_next_rotation()

    while True:
        # Find who is on-duty
        next_user = get_user_by_seq(next_rotation)

        # If no user is found, reset to zero
        if next_user is None:
            next_rotation = 0
            break

        # If selected user is in vacation, increment rotation seq
        if next_user.get('is_vacation', False):
            next_rotation += 1
        else:
            break

    # Update current rotation
    set_current_rotation(next_rotation)

    return next_rotation


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
    end_date = parse(end_date).replace(hour=23, minute=59)
    vacation_hash = _get_vacation_hash(email, start_date, end_date)

    # Check existing vacation
    vacation = get_vacation_by_hash(vacation_hash)

    if vacation is not None:
        raise KeyError

    utf_start_date = _get_utf_midnight(start_date)
    utf_end_date = _get_utf_midnight(end_date)
    result = mongo.db.users.update_one(
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
    _sync_vacation(email)
    return result


def get_vacation_by_hash(vacation_hash):
    return mongo.db.users.find_one(
        {'vacations.hash': vacation_hash}
    )


def delete_vacation(email, vacation_hash):
    try:
        result = mongo.db.users.update_one(
            {'email': email},
            {'$pull': {
                'vacations': {
                    'hash': vacation_hash
                }
            }},
            upsert=False
        )
        _sync_vacation(email)
        return result

    except Exception as e:
        print(e)


def get_all_settings():
    result = mongo.db.settings.find_one()

    if result is None:
        result = {
            'email_settings': {
                'from_email': current_app.config.get('MAIL_DEFAULT_SENDER'),
                'subject': current_app.config.get('MAIL_DEFAULT_SUBJECT'),
                'body': 'Congratulations, {{ display_name }}! You are ISR support rotation today.'
            }
        }

        mongo.db.settings.insert_one(result)

    return result


def get_email_settings():
    result = get_all_settings().get('email_settings')
    return result


def update_email_settings(from_email, subject, body):
    settings = get_all_settings()

    email_settings = {
        'email_settings': {
            'from_email': from_email,
            'subject': subject,
            'body': body
        }
    }

    return mongo.db.settings.find_one_and_update(
        {'_id': settings['_id']},
        {'$set': email_settings}
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
    :return: string
    """
    hash_key = (email, start_date, end_date)
    return str(hash(hash_key))


def _sync_all_vacation() -> None:
    """
    Update is_vacation property based on vacations across all users
    :return: None
    """
    users = get_all_user()
    for usr in users:
        _sync_vacation(usr['email'])

    pass


def _sync_vacation(email) -> None:
    """
    Update is_vacation property based on vacations
    :param email:
    :return: None
    """
    usr = get_user(email)
    now = datetime.now()
    is_vacation = False

    if usr.get('vacations'):
        for vacation in usr.get('vacations'):
            is_vacation = vacation.get('end_date') > now > vacation.get('start_date')
            if is_vacation:
                break

    if usr.get('is_vacation') is None or usr.get('is_vacation') != is_vacation:
        mongo.db.users.update_one(
            {'email': usr['email']},
            {'$set': {'is_vacation': is_vacation}}
        )

    pass


def _sync_seq():
    _sync_all_vacation()
    on_duty_users = get_all_on_duty_user()

    pass


