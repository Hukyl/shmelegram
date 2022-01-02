from flask import render_template, session, Blueprint, make_response

from shmelegram.views.auth import logged_in
from shmelegram.models import User


bp = Blueprint('chat', __name__, url_prefix='/')


@bp.route('', methods=('GET', ))
@logged_in
def index():
    user = User.get(session['user_id'])
    chats = sorted(
        user.chats.all(), key=lambda x: x.messages.first().created_at, 
        reverse=True
    )
    response = make_response(
        render_template('chat.html', user=user, chats=chats)
    )
    response.set_cookie('userID', str(user.id), max_age=30)  # 30 seconds
    return response
