from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, username, is_active, is_anonymous, is_authenticated):
        self.username = username
        self.param = dict(is_active=is_active, is_anonymous=is_anonymous, is_authenticated=is_authenticated)

    def __repr__(self):
        return self.username

    @property
    def is_active(self):
        return self.param.get('is_active')

    @property
    def is_anonymous(self):
        return self.param.get('is_anonymous')

    @property
    def is_authenticated(self):
        return self.param.get('is_authenticated')

    def get_id(self):
        return self.username

