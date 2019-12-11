from pytest import fixture

from wallet.model.user import User


@fixture(scope='session')
def app():
    from wallet.core import create_app
    return create_app(compact=True)


@fixture
def context(app):
    with app.app_context():
        yield app


@fixture
def user(context):
    assert context
    return User.query.filter_by(name='chaoyi').one()
