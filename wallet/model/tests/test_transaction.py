from datetime import datetime

from pytest import fixture

from wallet.core import db
from wallet.model.account import Account, AccountType
from wallet.model.enums import Currency, Timezone
from wallet.model.transaction import Category, Transaction
from wallet.model.user import User


def test_create_transaction(user):
    account = Account.create(user, 'test', AccountType.ASSET)
    category = Category.create(user, 'test')
    txn = Transaction.create(user, 'test', category, datetime.utcnow(), Timezone.US)
    txn.add_entry(account, 6.07, Currency.USD)
    txn.add_entry(account, 7.58, Currency.USD)
    txn.finish()
    db.session.flush()
    assert txn.amount == 13.65
    assert len(txn.entries) == 3


def test_category_list(user):
    assert Category.get_list(user)


@fixture
def user(context):
    assert context
    return User.query.filter_by(name='chaoyi').one()
