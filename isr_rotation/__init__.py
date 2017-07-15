from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Flask
app = Flask(__name__)
app.config.from_object('isr_rotation.config')

# Database
engine = create_engine(app.config.get('DATABASE_URI'), echo=False)
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = session.query_property()

# Blueprints (Controller)
from blueprints.controller import bp

app.register_blueprint(bp)
