from wallet.model.account import Account


def test_account_list(user):
    assert Account.get_list(user)
