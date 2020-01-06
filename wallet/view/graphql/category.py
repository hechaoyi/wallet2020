from flask_login import current_user
from graphene import Int, ObjectType, String

from wallet.model.category import Category as CategoryModel


class Category(ObjectType):
    id = Int()
    name = String()

    @staticmethod
    def get_list():
        return CategoryModel.get_list(current_user)
