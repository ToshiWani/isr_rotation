from flask import current_app
from flask_pymongo import PyMongo, ASCENDING, DESCENDING
from dateutil.parser import isoparse, parse
from datetime import timedelta, timezone, datetime
import shortuuid
from typing import Optional
import hashlib

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
    _sync_all_vacation()
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
            'vacations': [],
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
    result = mongo.db.users.update_one(
        {'email': email},
        {'$set': {'is_duty': is_duty, 'seq': seq}}
    )
    _sync_vacation(email)
    return result


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
    current_seq = get_current_rotation()
    return mongo.db.users.find_one({'seq': current_seq})


# region Holiday


def upasert_holiday(date, remarks):
    start_datetime = parse(date)
    holiday_id = _get_holiday_hash(start_datetime)

    return mongo.db.holidays.update_one(
        {'holiday_id': holiday_id},
        {
            '$set': {
                'date': start_datetime,
                'remarks': remarks,
                'holiday_id': holiday_id
            }
        },
        upsert=True
    )


def get_holidays():
    data = mongo.db.holidays.find().sort('date')
    result = []
    for d in data:
        result.append({
            'holiday_id': d.get('holiday_id'),
            'date': d.get('date'),
            'remarks': d.get('remarks')
        })

    return result


def is_holiday_now() -> bool:
    holidays = get_holidays()
    is_holiday = False
    for h in holidays:
        is_holiday = h['date'].strftime('%x') == datetime.now().strftime('%x')
        if is_holiday:
            break

    return is_holiday


def delete_holiday(holiday_id):
    return mongo.db.holidays.delete_one({'holiday_id': holiday_id})

# endregion


def add_vacation(email, start_date, end_date, remarks):
    start_datetime = parse(start_date)
    end_datetime = parse(end_date).replace(hour=23, minute=59)
    vacation_hash = _get_vacation_hash(email, start_datetime, end_datetime)

    # Check existing vacation
    vacation = get_vacation_by_hash(vacation_hash)

    if vacation is not None:
        raise KeyError('Start date and end date are duplicated')

    result = mongo.db.users.update_one(
        {'email': email},
        {'$push': {
            'vacations': {
                'hash': vacation_hash,
                'start_date': start_datetime,
                'end_date': end_datetime,
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
        # Seeding default settings
        result = {
            'email_settings': {
                'from_email': current_app.config.get('MAIL_DEFAULT_SENDER'),
                'subject': current_app.config.get('MAIL_DEFAULT_SUBJECT'),
                'body': 'Congratulations, ${display_name}!\r\n'
                        'You are ISR support rotation today.\r\n'
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

# region Logging


def get_log(limit=100):
    result = mongo.db.logs.find().sort('timestamp', DESCENDING).limit(limit)
    return result


def purge_log(days_older: int) -> int:
    result = 0
    if days_older > 0:
        older_than = datetime.now() - timedelta(days=days_older)
        logs = mongo.db.logs
        query = logs.delete_many({'timestamp': {'$lt': older_than}})
        result = query.raw_result.get('n', 0)

    return result


# endregion

# region Private


def _get_holiday_hash(holiday_date: datetime):
    """
    Create hash for holiday
    :param date:
    :return:
    """
    hash_key = f'{holiday_date}'.encode('utf-8')
    return hashlib.md5(hash_key).hexdigest()


def _get_vacation_hash(email: str, start_date: datetime, end_date: datetime):
    """
    Create hash for vacation
    :param email: email
    :param start_date: datetime
    :param end_date: datetime
    :return: string
    """
    hash_key = f'{email}|{start_date}|{end_date}'.encode('utf-8')
    return hashlib.md5(hash_key).hexdigest()


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

# endregion

