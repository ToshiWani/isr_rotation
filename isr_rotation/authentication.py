from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager
from isr_rotation.user import User


ldap3 = LDAP3LoginManager()
login_manager = LoginManager()
users = {}


def authenticate(username, password):
    result = ldap3.authenticate_direct_credentials(username, password)
    return result


def get_ldap_user(username):
    user = ldap3.get_user_info_for_username(username)
    return user


@login_manager.user_loader
def load_user(id):
    if id in users:
        return users[id]
    return None


@ldap3.save_user
def save_user(dn, username, data, memberships):
    user = User(dn, username, data)
    users[dn] = user
    return user
