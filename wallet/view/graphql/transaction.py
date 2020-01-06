from flask import current_app
from flask_login import current_user
from graphene import Boolean, DateTime, Float, InputObjectType, Int, List, Mutation, String

from wallet.core import db
from wallet.model.account import Account as AccountModel, AccountType
from wallet.model.category import Category as CategoryModel
from wallet.model.entry import Entry as EntryModel
from wallet.model.enums import Currency, Timezone
from wallet.model.transaction import Transaction as TransactionModel


class EntryInput(InputObjectType):
    account = Int(required=True)
    inflow = Boolean(required=True)
    amount = Float(required=True)
    currencyUS = Boolean(required=True)
    description = String()
    merge_entry = Int()


class TransactionInput(InputObjectType):
    description = String(required=True)
    category = Int(required=True)
    time = DateTime(required=True)
    timezoneUS = Boolean(required=True)
    items = List(EntryInput, required=True)


class AddTransaction(Mutation):
    class Arguments:
        input = TransactionInput(required=True)

    ok = Boolean()

    @staticmethod
    def mutate(*_, input):
        description, category, time, timezone, items = _validate_input(input)
        txn = TransactionModel.create(current_user, description, category, time, timezone)
        for account, amount, currency, name, merge_entry in items:
            txn.add_entry(account, amount, currency, name=name, auto_merge=merge_entry)
        txn.finish()
        db.session.commit()
        current_app.logger.info(f'transaction created: {txn}')
        for i, entry in enumerate(txn.entries):
            current_app.logger.info(f'associated entry{i + 1}: {entry}')
        return AddTransaction(ok=True)


def _validate_input(input):
    description = input.description.strip()
    if not description:
        raise ValueError('必填：说明')
    category = CategoryModel.query.get(input.category)
    if category.user_id != current_user.id:
        raise ValueError('必填：分类')
    time = input.time.replace(tzinfo=None)  # UTC time assumed
    timezone = Timezone.US if input.timezoneUS else Timezone.CN
    items = []
    for item in input.items:
        account = AccountModel.query.get(item.account)
        if account.user_id != current_user.id:
            raise ValueError('必填：账户')
        amount = item.amount
        if amount <= 0:
            raise ValueError('金额必须为正数')
        if (account.type != AccountType.LIABILITY and not item.inflow) or (
                account.type == AccountType.LIABILITY and item.inflow):
            amount = -amount
        currency = Currency.USD if item.currencyUS else Currency.RMB
        name = item.description.strip() if item.description and item.description.strip() else None
        merge_entry = EntryModel.query.get(item.merge_entry) if item.merge_entry else None
        if merge_entry and merge_entry.account_id != account.id:
            merge_entry = None
        items.append((account, amount, currency, name, merge_entry))
    return description, category, time, timezone, items
