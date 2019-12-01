from wallet.core import db
from wallet.model.enums import Currency
from wallet.util.analysis import cached_exchange_rate as exchange_rate


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    successor_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    name = db.Column(db.String(32), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.IntEnum(Currency), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=db.utcnow)
    updated = db.Column(db.DateTime, onupdate=db.utcnow)
    # relationships
    successor = db.relationship('Entry', remote_side=[id], backref='predecessors')

    def __repr__(self):
        return (f'<Entry {self.name!r} {self.account.name!r} '
                f'{self.currency.symbol}{self.amount}>')

    @property
    def usd_amount(self):
        if self.currency == Currency.USD:
            return self.amount
        return self.amount / exchange_rate()

    @classmethod
    def create(cls, account, name, amount, currency, transaction=None):
        return cls(account=account, name=name, amount=amount, currency=currency,
                   transaction=transaction, active=(amount != 0))

    @classmethod
    def merge(cls, *assets):
        assert len(assets) > 1
        assert len({asset.account for asset in assets}) == 1
        assert len({asset.currency for asset in assets}) == 1
        asset = max(assets, key=lambda e: abs(e.amount))
        amount = sum(asset.amount for asset in assets)
        successor = Entry.create(asset.account, asset.name, round(amount, 2), asset.currency)
        for asset in assets:
            asset.active = False
            asset.successor = successor
