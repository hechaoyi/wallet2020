from flask import current_app
from flask_login import current_user
from graphene import Boolean, Int, Mutation, String

from wallet.core import db
from wallet.model.config import Config


class AddTransactionTemplate(Mutation):
    class Arguments:
        template = String(required=True)

    ok = Boolean()
    template_id = Int()

    @staticmethod
    def mutate(*_, template):
        template_id = Config.add_transaction_template(current_user, template)
        db.session.commit()
        current_app.logger.info(f'transaction template created: {template}')
        return AddTransactionTemplate(ok=True, template_id=template_id)


class DelTransactionTemplate(Mutation):
    class Arguments:
        template_id = String(required=True)

    ok = Boolean()

    @staticmethod
    def mutate(*_, template_id):
        Config.del_transaction_template(current_user, template_id)
        db.session.commit()
        current_app.logger.info(f'transaction template removed: {template_id}')
        return DelTransactionTemplate(ok=True)
