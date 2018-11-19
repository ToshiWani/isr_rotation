SECRET_KEY = ''
DEBUG = True
ENABLE_WEEKEND = True
#
# Login
#
DEBUG_BYPASS_LOGIN = False
DEBUG_BYPASS_USERNAME = ''   # Example: your@email.com
ADMINS = []     # Example: ['your@email.com', 'anyone@email.com']
#
# Log level.  Enter DEBUG or INFO
#
LOG_LEVEL = 'INFO'
#
# Mongo DB
#
MONGO_URI = ''  # Example:  mongodb://localhost:27017/myDatabase
#
# Mongo DB Logger (MongoHandler)
#
MONGO_HANDLER_HOST = ''     # Example - 'mongodb://localhost:27017'
MONGO_HANDLER_DATABASE_NAME = ''    # Example - 'myDatabase'
#
# Mailer
#
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_DEFAULT_SENDER = None
MAIL_MAX_EMAILS = None
MAIL_ASCII_ATTACHMENTS = False
MAIL_DEFAULT_SUBJECT = 'ISR Rotation'
#
# LDAP
#
# Hostname of your LDAP Server
LDAP_HOST = 'yourldap.com'
# Base DN of your directory
LDAP_BASE_DN = 'DC=yourdomain,DC=com'
# Users DN to be prepended to the Base DN
LDAP_USER_DN = 'OU=users'
# The RDN attribute for your user schema on LDAP
LDAP_USER_RDN_ATTR = 'CN'
# The Attribute you want users to authenticate to LDAP with.
LDAP_USER_LOGIN_ATTR = 'mail'
# The Username to bind to LDAP with
LDAP_BIND_USER_DN = 'domain\\username'
# The Password to bind to LDAP with
LDAP_BIND_USER_PASSWORD = 'yourpassword'
# Instead of searching for a DN of a user you can instead bind directly to the directory.
# This is useful if you need to authenticate users with windows domain notation
LDAP_BIND_DIRECT_CREDENTIALS = True
