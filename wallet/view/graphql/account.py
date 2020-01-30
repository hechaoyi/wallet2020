from collections import defaultdict

from flask import g
from flask_login import current_user
from graphene import Float, Int, List, ObjectType, String

from wallet.model.account import Account as AccountModel
from wallet.model.entry import Entry as EntryModel
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
            entries = defaultdict(list)
            for entry in EntryModel.get_list(current_user):
                entries[entry.account].append(entry)
            g.active_entries = entries
        return g.active_entries[parent]

    @staticmethod
    def get_list():
        return AccountModel.get_list(current_user)
