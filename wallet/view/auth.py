from flask import Blueprint, abort, request
from flask_login import LoginManager, login_user, logout_user

from wallet.model.user import User

bp = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.user_loader(lambda user_id: User.query.get(int(user_id)))


@bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    user = User.query.filter_by(name=username).first()
    if user and user.chk_password(password):
        login_user(user)
        return 'OK'
    abort(401)


@bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return 'OK'
