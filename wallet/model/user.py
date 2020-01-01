from werkzeug.security import check_password_hash, generate_password_hash

from wallet.core import db
from wallet.model.account import Account, AccountType
from wallet.model.category import Category


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    default_equity_account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    # relationships
    default_equity_account = db.relationship('Account', foreign_keys=[default_equity_account_id], post_update=True)
    # for flask-login
    is_active = True
    is_authenticated = True
    is_anonymous = False

    def __repr__(self):
        return f'<User {self.name!r}>'

    def get_id(self):  # for flask-login
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def chk_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    @classmethod
    def create(cls, name):
        user = db.save(cls(name=name))
        user.default_equity_account = Account.create(user, '权益', AccountType.EQUITY)
        Account.create(user, '债务', AccountType.EQUITY)
        Account.create(user, '固定资产', AccountType.ASSET)
        for name in ('调整', '收益', '损失', '工资', '奖金', '转账', '借贷',
                     '日常', '住房', '交通', '购物', '娱乐', '学习', '工作', '社交', '健康'):
            Category.create(user, name)
        return user
