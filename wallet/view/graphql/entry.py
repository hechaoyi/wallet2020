from graphene import Float, Int, ObjectType, String


class Entry(ObjectType):
    id = Int()
    name = String()
    amount = Float()
    currency = Int()
    currency_symbol = String()

    @staticmethod
    def resolve_currency_symbol(parent, _):
        return parent.currency.symbol
