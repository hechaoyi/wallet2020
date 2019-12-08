from wallet.core import db
from wallet.model.user import User


def test_user_without_crash(context):
    assert context
    assert User.query.filter_by(name='chaoyi').one().name == 'chaoyi'


def test_create_new_user(context):
    assert context
    user = User.create('test')
    db.session.flush()
    assert user.default_equity_account.id
