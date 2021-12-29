from flask import render_template, session, Blueprint, make_response

from shmelegram.views.auth import logged_in
from shmelegram.models import User


bp = Blueprint('chat', __name__, url_prefix='/')


@bp.route('', methods=('GET', ))
@logged_in
def index():
    user_id = session['user_id']
    response = make_response(
        render_template('chat.html', user=User.get(user_id))
    )
    response.set_cookie('userID', str(user_id), max_age=30)  # 30 seconds
    return response
