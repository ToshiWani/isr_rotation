from flask import Flask

# Flask
app = Flask(__name__)
app.config.from_object('isr_rotation.config')

# Blueprints
from isr_rotation.blueprints.main import bp

app.register_blueprint(bp)
