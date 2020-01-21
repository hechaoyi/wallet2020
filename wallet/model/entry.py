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
    name = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.IntEnum(Currency), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=db.utcnow)
    updated = db.Column(db.DateTime, onupdate=db.utcnow)
    # relationships
    account = db.relationship('Account', back_populates='_entries')
    transaction = db.relationship('Transaction', back_populates='entries')
    successor = db.relationship('Entry', back_populates='predecessors', remote_side=[id])
    predecessors = db.relationship('Entry', back_populates='successor')

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
        amount = round(amount, 2)
        entry = cls(account=account, name=name, amount=amount, currency=currency,
                    transaction=transaction, active=(amount != 0), pending=pending)
        if auto_merge:
            if isinstance(auto_merge, list):
                cls.merge(entry, *auto_merge)
            else:
                cls.merge(entry, auto_merge, primary=auto_merge)
        return entry

    @classmethod
    def merge(cls, *assets, primary=None, name=None):
        assert len(assets) > 1
        assert len({(asset.account, asset.currency) for asset in assets}) == 1
        assert not any(asset.pending for asset in assets)
        amount = sum(asset.amount for asset in assets)
        primary = primary if primary else max(assets,
                                              key=lambda e: e.amount if amount >= 0 else -e.amount)
        successor = cls.create(primary.account,
                               name if name else primary.name,
                               amount, primary.currency)
        for asset in assets:
            asset.active = False
            asset.successor = successor
        return successor

    @classmethod
    def get_list(cls, user):
        return (cls.query.filter_by(active=True)
                .join(cls.account).filter_by(user=user)
                .order_by(cls.created).all())

    def split(self, name, amount):
        assert amount != 0
        Entry.create(self.account, name, -amount, self.currency, auto_merge=self)
        return db.save(Entry.create(self.account, name, amount, self.currency))

    def modify_amount(self, new_amount):
        assert self.active
        if len(self.transaction.entries) == 2:
            other = next(e for e in self.transaction.entries
                         if e != self and e.active and e.currency == self.currency)
        else:
            other = next(e for e in self.transaction.entries
                         if e != self and e.active and e.currency == self.currency
                         and e.account == self.account.user.default_equity_account)
        if self.account.type.is_debit == other.account.type.is_debit:
            other.amount -= round(new_amount - self.amount, 2)
        else:
            other.amount += round(new_amount - self.amount, 2)
        other.active = (other.amount != 0)
        self.amount = round(new_amount, 2)
        self.active = (self.amount != 0)
        self.transaction.finish()
