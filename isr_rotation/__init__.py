from flask import Flask, request
from isr_rotation.blueprints.main import bp as main_bp
from isr_rotation.blueprints.api import bp as api_bp
from isr_rotation.database import mongo
from isr_rotation.mailer import mail
from isr_rotation.authentication import ldap3, login_manager
from log4mongo.handlers import MongoHandler


# Flask
app = Flask(__name__)
app.config.from_object('isr_rotation.config')

# Logging
host = app.config.get('MONGO_URI', 'mongodb://localhost:27017')
database_name = app.config.get('MONGO_HANDLER_DATABASE_NAME', 'isr_rotation')
handler = MongoHandler(host=host, database_name=database_name)
app.logger.addHandler(handler)

# MongoDB
mongo.init_app(app)

# Mailer
mail.init_app(app)

# Login
ldap3.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "main.login"

# Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')


app.logger.info('Hello! ISR Rotation has been started!')

