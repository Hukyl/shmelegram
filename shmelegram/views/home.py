"""
This module introduces home views
Defines following view functions:
    - `index` ('/home/' url)
    - `about` ('/home/about/' url)
"""

from flask import Blueprint, render_template

bp = Blueprint('home', __name__, url_prefix='/home')


@bp.route('/', methods=('GET', ))
def index():
    """Render home index template"""
    return render_template('home/index.html', active_page='home')


@bp.route('/about', methods=('GET', ))
def about():
    """Render home about template"""
    return render_template('home/about.html', active_page='about')
