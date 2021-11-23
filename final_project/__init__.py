from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

from final_project.config import Config


app = Flask(__name__)
MIGRATION_DIR = 'final_project/migrations'

app.config.from_object(Config)

db = SQLAlchemy(app, session_options={'autocommit': True})
migrate = Migrate(app, db, directory=MIGRATION_DIR)

socketio = SocketIO(app)

from .models import *
