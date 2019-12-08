from enum import IntEnum

from wallet.core import db
from wallet.model.entry import Entry


class AccountType(IntEnum):
    ASSET = 1
    LIABILITY = 2
    EQUITY = 3


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    type = db.Column(db.IntEnum(AccountType), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=db.utcnow)
    updated = db.Column(db.DateTime, onupdate=db.utcnow)
    # relationships
    user = db.relationship('User', foreign_keys=[user_id])
    _entries = db.relationship('Entry', backref='account', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='account_user_name_key'),
    )

    def __repr__(self):
        return f'<Account {self.name!r} {self.type.name}>'

    @classmethod
    def create(cls, user, name, type_):
        return db.save(cls(user=user, name=name, type=type_))

    @classmethod
    def get_list(cls, user):
        count = db.session.query(
            Entry.account_id.label('account_id'),
            db.func.count().label('count')
        ).group_by(Entry.account_id).subquery()
        return (cls.query.filter_by(user=user)
                .outerjoin(count, cls.id == count.c.account_id)
                .order_by(count.c.count.desc().nullslast()).all())
