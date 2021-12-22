import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_restful import Api

from shmelegram.config import Config, MIGRATION_DIR


app = Flask(__name__, instance_relative_config=False)
app.config.from_object(Config)

db = SQLAlchemy(app, session_options={'autocommit': True})
migrate = Migrate(app, db, directory=MIGRATION_DIR)

socketio = SocketIO(app)

api = Api()

os.makedirs(app.instance_path, exist_ok=True)

from .models import Chat, User, Message
from .views import chat, home, auth
from .rest_api import (
    bp as rest_bp, chat as chat_api, user as user_api, 
    message as message_api
)


api.init_app(rest_bp)

app.register_blueprint(chat.bp)
app.register_blueprint(home.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(rest_bp)


@app.after_request
def flush_db(request):
    db.session.flush()
    return request
