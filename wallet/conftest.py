from pytest import fixture


@fixture(scope='session')
def app():
    from wallet.core import create_app
    return create_app(compact=True)


@fixture
def context(app):
    with app.app_context():
        yield app
