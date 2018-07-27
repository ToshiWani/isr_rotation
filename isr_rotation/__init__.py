from flask import Flask
from flask_pymongo import PyMongo


# Flask
app = Flask(__name__)
app.config.from_object('isr_rotation.config')

mongo = PyMongo(app)


# Blueprints
from isr_rotation.blueprints.main import bp as main_bp
from isr_rotation.blueprints.api import bp as api_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')

