from datetime import datetime

from wallet.core import db
from wallet.model.account import Account, AccountType
from wallet.model.category import Category
from wallet.model.entry import Entry
from wallet.model.enums import Currency, Timezone
from wallet.model.transaction import Transaction


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
