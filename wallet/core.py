from datetime import datetime
from logging import INFO
from os import getenv

from flask import Flask
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
        SQLALCHEMY_DATABASE_URI=getenv('DATABASE_URL', ''),
        SQLALCHEMY_ECHO=int(getenv('SQL_ECHO', '0')),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    app.logger.setLevel(INFO)


def _init_components(app):
    db.init_app(app)
    Migrate(app, db)

    from wallet.model.m1 import M1Portfolio
    models = [
        M1Portfolio,
    ]

    @app.route('/')
    def hello():
        return {'m1': [e.rate for e in M1Portfolio.query.all()]}

    app.shell_context_processor(lambda: {'db': db, **{m.__name__: m for m in models}})
