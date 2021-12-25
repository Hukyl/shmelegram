from functools import wraps

from flask import (
    Blueprint, flash, redirect, render_template, request, 
    session, url_for, g
)

from shmelegram.models import User
from shmelegram import db, utils


def logged_in(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login', next=request.endpoint))
        return func(*args, **kwargs)
    return inner


bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        if not utils.validate_username(username):
            error = "Invalid username"
        elif not utils.validate_password(password):
            error = "Invalid password"
        elif User.username_exists(username):
            error = "User with this username alraedy exists."
        if not error:
            try:
                user = User(username=username, password=password)
                user.save()
            except Exception:
                error = 'Unexpected error occurred, try again later'
            else:
                flash('User successfully created', 'success')
                return redirect(url_for('auth.login'))
        flash(error, 'danger')
    return render_template('auth/register.html', form=request.form, active_page='auth')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        error = None
        if not username:
            error = "Invalid username"
        elif not password:
            error = "Invalid password"
        elif not User.username_exists(username):
            error = "No user with such username exists"
        if not error:
            user = User.get_by_username(username)
            if user.check_password(password):
                session['user_id'] = user.id
                return redirect(url_for('chat.index'))
            error = "Passwords do not match"
        flash(error, 'danger')
    return render_template('auth/login.html', form=request.form, active_page='auth')


@bp.before_app_request
def load_user():
    user_id = session.get("user_id") 
    if user_id:
        g.user = User.get(user_id)
