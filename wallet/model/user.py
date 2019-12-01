from wallet.core import db
from wallet.model.account import Account, AccountType


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    default_equity_account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    # relationships
    default_equity_account = db.relationship('Account', foreign_keys=[default_equity_account_id])

    def __repr__(self):
        return f'<User {self.name!r}>'

    @classmethod
    def create(cls, name):
        user = db.save(cls(name=name))
        equity = Account.create(user, '权益', AccountType.EQUITY)
        db.session.flush()
        user.default_equity_account = equity
        return user
