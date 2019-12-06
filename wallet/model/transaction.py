from collections import defaultdict

from wallet.core import db
from wallet.model.account import AccountType
from wallet.model.entry import Entry
from wallet.model.enums import Currency, Timezone
from wallet.util.swapsy import cached_exchange_rate as exchange_rate


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    currency = db.Column(db.IntEnum(Currency), nullable=False, default=Currency.USD)
    exchange_rate_assumed = db.Column(db.Float)
    occurred_utc = db.Column(db.DateTime, nullable=False)
    occurred_tz = db.Column(db.IntEnum(Timezone), nullable=False)
    # relationships
    user = db.relationship('User')
    category = db.relationship('Category')
    entries = db.relationship('Entry', backref='transaction')

    def __repr__(self):
        return (f'<Transaction {self.name!r} {self.category.name!r} '
                f'{self.currency.symbol}{self.amount} '
                f'{self.occurred_utc.isoformat(timespec="seconds")}>')

    @classmethod
    def create(cls, user, name, category, occurred_utc, occurred_tz):
        return db.save(cls(user=user, name=name, category=category,
                           occurred_utc=occurred_utc, occurred_tz=occurred_tz))

    def add_entry(self, account, amount, currency, name=None):
        assert amount != 0
        Entry.create(account, (name if name else self.name), amount, currency, self)

    def finish(self, name=None):
        amounts = defaultdict(int)
        for entry in self.entries:
            if entry.account.type == AccountType.ASSET:
                amounts[entry.currency] += entry.amount
            else:
                amounts[entry.currency] -= entry.amount
        amounts_without_zero = {c: a for c, a in amounts.items() if a != 0}
        if len(amounts_without_zero) == 1:
            currency, amount = next(iter(amounts_without_zero.items()))
            self.add_entry(self.user.default_equity_account, round(amount, 2), currency, name)
        elif len(amounts_without_zero) == 2:
            self.exchange_rate_assumed = round(-amounts[Currency.RMB] / amounts[Currency.USD], 4)
            assert abs(self.exchange_rate_assumed / exchange_rate() - 1) < .01
        entry = max(self.entries, key=lambda e: abs(e.usd_amount))
        self.amount = abs(entry.amount)
        self.currency = entry.currency


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    # relationships
    user = db.relationship('User')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='category_user_name_key'),
    )

    def __repr__(self):
        return f'<Category {self.name!r}>'

    @classmethod
    def create(cls, user, name):
        return db.save(cls(user=user, name=name))
