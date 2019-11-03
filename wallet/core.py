from datetime import datetime
from logging import INFO
from os import environ

from flask import Flask, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
db.utcnow = datetime.utcnow


def create_app():
    app = Flask(__name__)
    _init_configurations(app)
    _init_components(app)
    app.logger.info('Started')
    return app


def _init_configurations(app):
    app.config.update(
        SQLALCHEMY_DATABASE_URI=environ['DATABASE_URL'],
        SQLALCHEMY_ECHO=app.debug,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        M1_USERNAME=environ['M1_USERNAME'],
        M1_PASSWORD=environ['M1_PASSWORD'],
        M1_ACCOUNT=environ['M1_ACCOUNT'],
    )
    app.logger.setLevel(INFO)


def _init_components(app):
    db.init_app(app)
    Migrate(app, db)

    from wallet.model.m1 import M1Portfolio
    models = [
        M1Portfolio,
    ]
    [m.init_app(app) for m in models if hasattr(m, 'init_app')]

    @app.shell_context_processor
    def shell_context():
        return {
            'db': db,
            **{m.__name__: m for m in models},
        }

    @app.route('/')
    def root():
        limit = request.args.get('limit', 10, int)
        return '\n'.join(
            f'{e.date}: {e.value:.2f}  -  {e.gain:+7.2f} ({e.rate:+.2f}%)'
            for e in M1Portfolio.net_value_series(limit)
        )
