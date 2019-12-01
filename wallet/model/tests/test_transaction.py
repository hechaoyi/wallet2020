from datetime import datetime

from pytest import fixture

from wallet.core import db
from wallet.model.account import Account
from wallet.model.enums import Currency, Timezone
from wallet.model.transaction import Category, Transaction
from wallet.model.user import User


def test_create_transaction(user):
    assert user
    category = Category.query.filter_by(user=user).first()
    account = Account.query.filter_by(user=user).first()
    txn = Transaction.create(user, 'testing', category, datetime.utcnow(), Timezone.US)
    txn.add_entry(account, 6.07, Currency.USD)
    txn.add_entry(account, 7.58, Currency.USD)
    txn.finish()
    db.session.flush()
    assert txn.amount == 13.65
    assert len(txn.entries) == 3


@fixture
def user(context):
    assert context
    return User.query.filter_by(name='chaoyi').one()
