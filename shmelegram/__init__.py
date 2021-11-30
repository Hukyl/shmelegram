from flask import Flask, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

from shmelegram.config import Config, MIGRATION_DIR


app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app, session_options={'autocommit': True})
migrate = Migrate(app, db, directory=MIGRATION_DIR)

socketio = SocketIO(app)

from .models import Chat, User, Message
from shmelegram.views import chat, home, auth

app.register_blueprint(chat.bp)
app.register_blueprint(home.bp)
app.register_blueprint(auth.bp)


@app.before_request
def load_user():
    user_id = session.get("user_id") 
    if user_id:
        g.user = User.query.get(user_id)
