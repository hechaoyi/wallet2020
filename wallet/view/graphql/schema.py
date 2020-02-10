from flask_login import current_user
from graphene import Int, List, ObjectType, Schema, String

from wallet.model.config import Config
from wallet.model.m1 import M1Portfolio
from wallet.view.graphql.account import Account
from wallet.view.graphql.category import Category
from wallet.view.graphql.config import AddTransactionTemplate, DelTransactionTemplate
from wallet.view.graphql.transaction import AddTransaction


class Query(ObjectType):
    health_check = String()
    accounts = List(Account)
    categories = List(Category)
    transaction_templates = String()
    m1 = List(String, name=String(default_value='Individual'), limit=Int(default_value=20))

    @staticmethod
    def resolve_health_check(*_):
        return 'success'

    @staticmethod
    def resolve_accounts(*_):
        return Account.get_list()

    @staticmethod
    def resolve_categories(*_):
        return Category.get_list()

    @staticmethod
    def resolve_transaction_templates(*_):
        return Config.get_transaction_templates(current_user)

    @staticmethod
    def resolve_m1(*_, name, limit):
        return [f'{e.date}: {e.value:.2f} - {e.gain:+7.2f} ({e.rate:+.2f}%)'
                for e in M1Portfolio.net_value_series(name, limit)]


class Mutation(ObjectType):
    add_transaction = AddTransaction.Field()
    add_transaction_template = AddTransactionTemplate.Field()
    del_transaction_template = DelTransactionTemplate.Field()


schema = Schema(query=Query, mutation=Mutation)
