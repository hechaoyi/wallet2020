from wallet.core import db
from wallet.model.enums import Currency
from wallet.util.swapsy import cached_exchange_rate as exchange_rate


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    pending = db.Column(db.Boolean, nullable=False)
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
    def create(cls, account, name, amount, currency, transaction=None, pending=False, auto_merge=None):
        entry = cls(account=account, name=name, amount=amount, currency=currency,
                    transaction=transaction, active=(amount != 0), pending=pending)
        if auto_merge:
            cls.merge(entry, auto_merge, primary=auto_merge)
        return entry

    @classmethod
    def merge(cls, *assets, primary=None):
        assert len(assets) > 1
        assert len({(asset.account, asset.currency) for asset in assets}) == 1
        assert not any(asset.pending for asset in assets)
        primary = primary if primary else max(assets, key=lambda e: abs(e.amount))
        amount = sum(asset.amount for asset in assets)
        successor = cls.create(primary.account, primary.name, round(amount, 2), primary.currency)
        for asset in assets:
            asset.active = False
            asset.successor = successor

    def split(self, name, amount):
        assert amount != 0
        db.save(Entry.create(self.account, name, amount, self.currency))
        Entry.merge(Entry.create(self.account, name, -amount, self.currency), self, primary=self)
