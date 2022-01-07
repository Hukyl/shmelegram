from datetime import datetime

from flask import Blueprint, make_response, render_template, session

from shmelegram.models import Message, User
from shmelegram.views.auth import logged_in

bp = Blueprint('chat', __name__, url_prefix='/')


def datetime_or_now(message: Message):
    if not message:
        return datetime.utcnow()
    return message.created_at



@bp.route('', methods=('GET', ))
@logged_in
def index():
    user = User.get(session['user_id'])

    chats = sorted(
        user.chats.all(), key=lambda x: datetime_or_now(x.messages.first()), 
        reverse=True
    )
    response = make_response(
        render_template('chat.html', user=user, chats=chats)
    )
    response.set_cookie('userID', str(user.id), max_age=30)  # 30 seconds
    return response
