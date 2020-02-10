from datetime import datetime

from pytest import raises

from wallet.core import db
from wallet.model.account import Account, AccountType
from wallet.model.category import Category
from wallet.model.entry import Entry
from wallet.model.enums import Currency, Timezone
from wallet.model.transaction import Transaction
from wallet.util.swapsy import cached_exchange_rate as exchange_rate


def test_create_transaction(user):
    account = Account.create(user, 'test', AccountType.ASSET)
    category = Category.create(user, 'test')
    prev_entry = Entry.query.filter_by(
        account=user.default_equity_account, active=True, currency=Currency.USD
    ).first()
    txn = Transaction.create(user, 'test', category, datetime.utcnow(), Timezone.US)
    txn.add_entry(account, 6.07, Currency.USD)
    txn.add_entry(account, 7.58, Currency.USD)
    txn.finish(auto_merge=prev_entry)
    db.session.flush()
    assert txn.amount == 13.65
    assert len(txn.entries) == 3
    assert not prev_entry.active
    assert prev_entry.amount + 13.65 == prev_entry.successor.amount


def test_create_transaction_with_currency_exchange(user):
    rate = exchange_rate() * 1.005
    account = Account.create(user, 'test', AccountType.ASSET)
    category = Category.create(user, 'test')
    txn = Transaction.create(user, 'test', category, datetime.utcnow(), Timezone.US)
    txn.add_entry(account, -5, Currency.USD)
    txn.add_entry(account, 5 * rate, Currency.RMB)
    txn.finish()
    db.session.flush()
    assert txn.amount == round(5 * rate, 2) and txn.currency == Currency.RMB
    assert len(txn.entries) == 4
    assert round(txn.exchange_rate_assumed, 2) == round(rate, 2)


def test_create_transaction_with_erroneous_currency_exchange(user):
    rate = exchange_rate() * 1.025
    account = Account.create(user, 'test', AccountType.ASSET)
    category = Category.create(user, 'test')
    txn = Transaction.create(user, 'test', category, datetime.utcnow(), Timezone.US)
    txn.add_entry(account, -8, Currency.USD)
    txn.add_entry(account, 8 * rate, Currency.RMB)
    with raises(AssertionError):
        txn.finish()
