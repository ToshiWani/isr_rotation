from flask import Flask
from isr_rotation.blueprints.main import bp as main_bp
from isr_rotation.blueprints.api import bp as api_bp
from isr_rotation.database import mongo
from isr_rotation.mailer import mail
from isr_rotation.authentication import ldap3, login_manager

# Flask
app = Flask(__name__)
app.config.from_object('isr_rotation.config')

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