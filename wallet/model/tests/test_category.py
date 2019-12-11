from wallet.model.category import Category


def test_category_list(user):
    assert Category.get_list(user)
