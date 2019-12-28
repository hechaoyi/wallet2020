from graphene import Float, Int, List, ObjectType, String

from wallet.model.account import Account as AccountModel
from wallet.model.user import User
from wallet.view.graphql.entry import Entry


class Account(ObjectType):
    id = Int()
    name = String()
    type = Int()
    type_name = String()
    balance_usd = Float()
    balance_rmb = Float()
    active_entries = List(Entry)

    @staticmethod
    def resolve_type_name(parent, _):
        return parent.type.display_name

    @staticmethod
    def get_list():
        user = User.query.filter_by(name='chaoyi').first()  # TODO
        accounts = AccountModel.get_list(user)
        return [a for a in accounts if a.balance_usd or a.balance_rmb]
