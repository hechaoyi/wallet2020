from graphene import Int, List, ObjectType, Schema, String

from wallet.model.m1 import M1Portfolio
from wallet.view.graphql.account import Account


class Query(ObjectType):
    accounts = List(Account)
    m1 = List(String, name=String(default_value='Individual'), limit=Int(default_value=20))

    @staticmethod
    def resolve_accounts(*_):
        return Account.get_list()

    @staticmethod
    def resolve_m1(*_, name, limit):
        return [f'{e.date}: {e.value:.2f} - {e.gain:+7.2f} ({e.rate:+.2f}%)'
                for e in M1Portfolio.net_value_series(name, limit)]


schema = Schema(query=Query)
