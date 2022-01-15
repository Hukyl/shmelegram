"""
This module introduces chat views.
Defines following view functions:
    - `index`
"""

from flask import Blueprint, make_response, render_template, session

from shmelegram.views.auth import logged_in


bp = Blueprint('chat', __name__, url_prefix='/')


@bp.route('', methods=('GET', ))
@logged_in
def index():
    """
    Get chat index template.
    Requires the user to be logged in, otherwise redirected to login.
    Sets cookie of 'userID'.
    """
    response = make_response(render_template('chat.html'))
    response.set_cookie('userID', str(session['user_id']), max_age=30)  # 30 seconds
    return response
