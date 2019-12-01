from wallet.model.user import User


def test_user_without_crash(context):
    assert context
    assert User.query.filter_by(name='chaoyi').one().name == 'chaoyi'
