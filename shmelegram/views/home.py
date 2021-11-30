from flask import render_template, Blueprint


bp = Blueprint('home', __name__, url_prefix='/home')


@bp.route('/', methods=('GET', ))
def index():
    return render_template('home/index.html', active_page='home')


@bp.route('/about', methods=('GET', ))
def about():
    return render_template('home/about.html', active_page='about')
