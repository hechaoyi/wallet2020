from graphene import Int, List, NonNull, ObjectType, Schema, String, relay

from wallet.model.m1 import M1Portfolio


class Query(ObjectType):
    node = relay.Node.Field()
    m1 = List(NonNull(String), limit=Int(default_value=10))

    @staticmethod
    def resolve_m1(*_, limit):
        return [f'{e.date}: {e.value:.2f} - {e.gain:+7.2f} ({e.rate:+.2f}%)'
                for e in M1Portfolio.net_value_series(limit)]


schema = Schema(query=Query)
