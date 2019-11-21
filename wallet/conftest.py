import os
import sys

from pytest import fixture

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))


@fixture(scope='session')
def app():
    from wallet.core import create_app
    return create_app()


@fixture
def context(app):
    with app.app_context():
        yield app
