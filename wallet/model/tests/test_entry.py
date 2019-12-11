from wallet.core import db
from wallet.model.account import Account, AccountType
from wallet.model.entry import Entry
from wallet.model.enums import Currency


def test_split(user):
    trunk = Entry.query.filter_by(account=user.default_equity_account, active=True).first()
    branch = trunk.split('test', 1.02)
    db.session.flush()
    assert branch.amount == 1.02 and not branch.predecessors
    assert not trunk.active
    assert round(trunk.amount - 1.02, 2) == trunk.successor.amount


def test_formula(user):
    def entries(currency):
        return (Entry.query.filter_by(active=True, currency=currency)
                .options(db.joinedload(Entry.account, innerjoin=True))
                .filter(Account.user == user).all())

    def amount(e):
        return +e.amount if e.account.type == AccountType.ASSET else -e.amount

    assert round(sum(amount(entry) for entry in entries(Currency.USD)), 2) == 0
    assert round(sum(amount(entry) for entry in entries(Currency.RMB)), 2) == 0
