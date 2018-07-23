from flask import Flask
from flask_pymongo import PyMongo


# Flask
app = Flask(__name__)
app.config.from_object('isr_rotation.config')

mongo = PyMongo(app)
users = mongo.db.user.find()

result = []

for u in users:
    result.append(u)


# Blueprints
from isr_rotation.blueprints.main import bp

app.register_blueprint(bp)
