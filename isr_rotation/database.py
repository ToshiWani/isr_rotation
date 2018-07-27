from isr_rotation import mongo


def get_all_user():
    return list(mongo.db.users.find())


def get_user(email):
    return next(iter(mongo.db.users.find({'email': email})), None)


def upsert_user(email, display_name):
    user = {'$set': {'email': email, 'display_name': display_name}}
    return mongo.db.users.update_one({'email': email}, user, upsert=True)


def delete_user(email):
    return mongo.db.users.delete_one({'email': email})


def delete_users(emails):
    query = {'email': {'$in': emails}}
    return mongo.db.users.delete_many(query)


