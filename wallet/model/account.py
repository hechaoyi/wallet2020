from enum import IntEnum

from flask_sqlalchemy import BaseQuery

from wallet.core import db
from wallet.model.entry import Entry
from wallet.model.enums import Currency


class AccountType(IntEnum):
    ASSET = 1
    LIABILITY = 2
    EQUITY = 3

    @property
    def is_debit(self):
        return self == AccountType.ASSET

    @property
    def display_name(self):
        return _ACCOUNT_TYPE_NAMES[self]


_ACCOUNT_TYPE_NAMES = {
    AccountType.ASSET: '资产',
    AccountType.LIABILITY: '负债',
    AccountType.EQUITY: '权益',
}


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    type = db.Column(db.IntEnum(AccountType), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=db.utcnow)
    updated = db.Column(db.DateTime, onupdate=db.utcnow)
    balance_usd = db.query_expression()
    balance_rmb = db.query_expression()
    # relationships
    user = db.relationship('User', foreign_keys=[user_id])
    _entries = db.relationship('Entry', back_populates='account', lazy='dynamic')
    # metadata
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='account_user_name_key'),
    )

    def __repr__(self):
        if self.balance_usd and self.balance_rmb:
            return f'<Account {self.name!r} {self.type.name} | ${self.balance_usd} + ¥{self.balance_rmb}>'
        if self.balance_usd:
            return f'<Account {self.name!r} {self.type.name} | ${self.balance_usd}>'
        if self.balance_rmb:
            return f'<Account {self.name!r} {self.type.name} | ¥{self.balance_rmb}>'
        return f'<Account {self.name!r} {self.type.name}>'

    @property
    def active_entries(self):
        return self._entries.filter_by(active=True).all()

    @classmethod
    def create(cls, user, name, type_):
        return db.save(cls(user=user, name=name, type=type_))

    @classmethod
    def get_list(cls, user):
        return cls.query.filter_by(user=user).with_balance().order_by_entry_count().all()


class AccountQuery(BaseQuery):
    def with_balance(self):
        balance = db.session.query(
            Entry.account_id.label('account_id'),
            db.func.sum(db.case([(Entry.currency == Currency.USD, Entry.amount)])).label('usd'),
            db.func.sum(db.case([(Entry.currency == Currency.RMB, Entry.amount)])).label('rmb'),
        ).filter_by(active=True).group_by(Entry.account_id).subquery('balance')
        return self.options(
            db.with_expression(Account.balance_usd, db.func.coalesce(balance.c.usd, 0)),
            db.with_expression(Account.balance_rmb, db.func.coalesce(balance.c.rmb, 0)),
        ).outerjoin(balance, Account.id == balance.c.account_id)

    def order_by_entry_count(self):
        count = db.session.query(
            Entry.account_id.label('account_id'),
            db.func.count().label('count'),
        ).group_by(Entry.account_id).subquery('count')  # TODO recent 3 months
        return (self.outerjoin(count, Account.id == count.c.account_id)
                .order_by(count.c.count.desc().nullslast(), Account.id))


Account.query_class = AccountQuery
