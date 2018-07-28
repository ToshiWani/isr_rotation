from flask_ldap3_login import LDAP3LoginManager


ldap3 = LDAP3LoginManager()


def authenticate(username, password):
    result = ldap3.authenticate_direct_credentials(username, password)
    return result


def get_ldap_user(username):
    user = ldap3.get_user_info_for_username(username)
    return user

