from collections import defaultdict

from flask import g
from graphene import Float, Int, List, ObjectType, String

from wallet.model.account import Account as AccountModel
from wallet.model.entry import Entry as EntryModel
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
    def resolve_active_entries(parent, _):
        if 'active_entries' not in g:
            user = User.query.filter_by(name='chaoyi').first()  # TODO
            entries = defaultdict(list)
            for entry in EntryModel.get_list(user):
                entries[entry.account].append(entry)
            g.active_entries = entries
        return g.active_entries[parent]

    @staticmethod
    def get_list():
        user = User.query.filter_by(name='chaoyi').first()  # TODO
        accounts = AccountModel.get_list(user)
        return [a for a in accounts if a.balance_usd or a.balance_rmb]
