import os

import eventlet
from flask import Flask
from flask_migrate import Migrate
from flask_restful import Api
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from shmelegram.utils.redis_client import RedisClient
from shmelegram.config import BaseConfig, TestConfig, Config

eventlet.monkey_patch()

app = Flask(__name__, instance_relative_config=False)
app.config.from_object(TestConfig if BaseConfig.TESTING else Config)

db = SQLAlchemy(app, session_options={'autocommit': True})
migrate = Migrate(app, db, directory=BaseConfig.MIGRATION_DIR)
redis_client = RedisClient.from_url(
    app.config['REDIS_URL'], decode_responses=True
)

socketio = SocketIO(app, engineio_logger=True, logger=True)

api = Api()

os.makedirs(app.instance_path, exist_ok=True)

from .models import Chat, Message, User
from .rest_api import bp as rest_bp
from .rest_api import chat as chat_api
from .rest_api import message as message_api
from .rest_api import user as user_api
from .views import auth, chat, home, messaging

api.init_app(rest_bp)

app.register_blueprint(chat.bp)
app.register_blueprint(home.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(rest_bp)


@app.after_request
def flush_db(request):
    db.session.flush()
    return request
