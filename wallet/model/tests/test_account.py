from pytest import fixture

from wallet.model.account import Account
from wallet.model.user import User


def test_account_list(user):
    assert Account.get_list(user)


@fixture
def user(context):
    assert context
    return User.query.filter_by(name='chaoyi').one()
