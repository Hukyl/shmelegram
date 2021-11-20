from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config


app = Flask(__name__)
app.config.from_config(Config)

db = SQLAlchemy(app)

from .models import *
