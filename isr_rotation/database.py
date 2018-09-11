from flask_pymongo import PyMongo
from dateutil.parser import isoparse
from datetime import timedelta, timezone, datetime


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
                'remarks': remarks
            }
        },
        upsert=True
    )


def add_vacation(start_date, end_date, remarks):
    # start = parse(start_date)
    # end = parse(end_date) + timedelta(days=1) + timedelta(seconds=-1)
    # return mongo.db.holidays.insert_one({
    #     'start_date': start,
    #     'end_date': end,
    #     'remarks': remarks
    # })
    pass


def get_holidays():
    data = mongo.db.holidays.find().sort('date')
    utc_diff = datetime.utcnow() - datetime.now()
    result = []
    for d in data:
        result.append({'date': d.get('date') - utc_diff, 'remarks': d.get('remarks')})

    return result
