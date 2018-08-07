from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager
from isr_rotation.user import User
import isr_rotation.database as db

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
def load_user(username):
    return users[username] if username in users else None


@ldap3.save_user
def save_user(dn, username, data, memberships):
    registered_user = db.get_user(username)

    if registered_user is None:
        return User(None,
                    is_active=False,
                    is_anonymous=True,
                    is_authenticated=False,
                    display_name=None)
    else:
        users[username] = User(username,
                               is_active=True,
                               is_anonymous=False,
                               is_authenticated=True,
                               display_name=registered_user.get('display_name'))
        return users[username]

