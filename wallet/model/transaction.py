from collections import defaultdict

from wallet.core import db
from wallet.model.account import AccountType
from wallet.model.entry import Entry
from wallet.model.enums import Currency, Timezone
from wallet.util.swapsy import cached_exchange_rate as exchange_rate


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    currency = db.Column(db.IntEnum(Currency), nullable=False, default=Currency.USD)
    exchange_rate_assumed = db.Column(db.Float)
    occurred_utc = db.Column(db.DateTime, nullable=False)
    occurred_tz = db.Column(db.IntEnum(Timezone), nullable=False)
    # relationships
    user = db.relationship('User')
    category = db.relationship('Category')
    entries = db.relationship('Entry', back_populates='transaction')

    def __repr__(self):
        return (f'<Transaction {self.name!r} {self.category.name!r} '
                f'{self.currency.symbol}{self.amount} '
                f'{self.occurred.isoformat(timespec="minutes")!r}>')

    @property
    def occurred(self):
        return self.occurred_tz.from_utc(self.occurred_utc)

    @classmethod
    def create(cls, user, name, category, occurred_utc, occurred_tz):
        return db.save(cls(user=user, name=name, category=category,
                           occurred_utc=occurred_utc, occurred_tz=occurred_tz))

    def add_entry(self, account, amount, currency, name=None, pending=False, auto_merge=None):
        assert amount != 0
        if not name:
            name = self.name if self.name else self.category.name
            # if amount > 0 and not auto_merge:
            #     name = f'{name} [{self.occurred.strftime("%y%m%d")}]'
        Entry.create(account, name, amount, currency, self, pending, auto_merge)

    @db.no_autoflush
    def finish(self, name=None, auto_merge=None):
        amounts = defaultdict(int)
        for entry in self.entries:
            if entry.account.type == AccountType.ASSET:
                amounts[entry.currency] += entry.amount
            else:
                amounts[entry.currency] -= entry.amount
        amounts_without_zero = {c: a for c, a in amounts.items() if a != 0}
        if len(amounts_without_zero) == 1:
            currency, amount = next(iter(amounts_without_zero.items()))
            self.add_entry(self.user.default_equity_account,
                           round(amount, 2), currency, name, False, auto_merge)
        elif len(amounts_without_zero) == 2:
            # TODO equity exchange
            self.exchange_rate_assumed = round(-amounts[Currency.RMB] / amounts[Currency.USD], 4)
            assert abs(self.exchange_rate_assumed / exchange_rate() - 1) < .01
        entry = max(self.entries, key=lambda e: abs(e.usd_amount))
        self.amount = abs(entry.amount)
        self.currency = entry.currency
