from flask_sqlalchemy import BaseQuery

from wallet.core import db
from wallet.model.transaction import Transaction


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    # relationships
    user = db.relationship('User')
    # metadata
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='category_user_name_key'),
    )

    def __repr__(self):
        return f'<Category {self.name!r}>'

    @classmethod
    def create(cls, user, name):
        return db.save(cls(user=user, name=name))

    @classmethod
    def get_list(cls, user):
        return cls.query.filter_by(user=user).order_by_transaction_count().all()


class CategoryQuery(BaseQuery):
    def order_by_transaction_count(self):
        count = db.session.query(
            Transaction.category_id.label('category_id'),
            db.func.count().label('count')
        ).group_by(Transaction.category_id).subquery('count')  # TODO recent 3 months
        return (self.outerjoin(count, Category.id == count.c.category_id)
                .order_by(count.c.count.desc().nullslast(), Category.id))


Category.query_class = CategoryQuery
