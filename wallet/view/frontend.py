from flask import Blueprint, current_app, redirect
from flask_login import current_user

bp = Blueprint('frontend', __name__)


@bp.route('/')
def root():
    return redirect('/u/home')


@bp.route('/u/<path:path>')
def frontend(path):
    if current_user.is_authenticated or path == 'login':
        return current_app.send_static_file('index.html')
    return redirect('/u/login')


@bp.app_errorhandler(404)
def not_found(_):
    response = current_app.send_static_file('index.html')
    response.status_code = 404
    return response
