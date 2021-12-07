from flask import render_template, session, Blueprint

from shmelegram.views.auth import logged_in


bp = Blueprint('chat', __name__, url_prefix='/')


@bp.route('', methods=('GET', ))
@logged_in
def index():
    return render_template('chat.html', user_id=session.get('user_id'))
