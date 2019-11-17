from datetime import datetime
from logging import INFO
from os import environ

from flask import Flask
from flask_graphql import GraphQLView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from redis import from_url

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
    )
    for key in [
        'M1_USERNAME', 'M1_PASSWORD', 'M1_ACCOUNT',
        'PLIVO_ID', 'PLIVO_TKN', 'PLIVO_SRC', 'PLIVO_DST',
        'SWAPSY_USERNAME', 'SWAPSY_PASSWORD',
    ]:
        app.config[key] = environ[key]
    app.logger.setLevel(INFO)


def _init_components(app):
    db.init_app(app)
    Migrate(app, db)
    app.redis = from_url(environ['REDIS_URL'])

    # models
    from wallet.model.m1 import M1Portfolio
    models = [
        M1Portfolio,
    ]
    [m.init_app(app) for m in models if hasattr(m, 'init_app')]

    # views
    from wallet.view.graphql import schema
    from wallet.view.plivo import bp as plivo_bp
    app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=app.debug))
    app.register_blueprint(plivo_bp, url_prefix='/plivo')

    # cli
    from wallet.util.swapsy import init_app as swapsy_init_app
    swapsy_init_app(app)
    app.shell_context_processor(lambda: {
        'db': db,
        **{m.__name__: m for m in models},
    })
