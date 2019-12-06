from datetime import datetime
from logging import INFO
from os import environ, fork, path

from flask import Flask
from flask.json import dumps
from flask_sqlalchemy import SQLAlchemy
from redis import from_url
from rq import Queue

db = SQLAlchemy()


def create_app(compact=False):
    app = Flask(__name__,
                static_url_path='',
                static_folder=path.abspath(path.dirname(__file__) + '/../ui/build'))
    _init_configurations(app)
    _init_components(app, compact)
    app.logger.info('Started %s', '[debug]' if app.debug else '')
    return app


def _init_configurations(app):
    app.config.update(
        SQLALCHEMY_DATABASE_URI=environ['DATABASE_URL'],
        SQLALCHEMY_ECHO=app.debug,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    for key in [
        'M1_USERNAME', 'M1_PASSWORD',
        'SWAPSY_USERNAME', 'SWAPSY_PASSWORD',
        'PLIVO_ID', 'PLIVO_TKN', 'PLIVO_SRC', 'PLIVO_DST',
    ]:
        app.config[key] = environ.get(key, '')
    app.web = 'gunicorn' in environ.get('SERVER_SOFTWARE', '')
    app.logger.setLevel(INFO)


def _init_components(app, compact):
    db.init_app(app)
    app.redis = from_url(environ['REDIS_URL'])
    app.queue = Queue(connection=app.redis)
    models = _init_models(app)
    if not compact:
        if app.debug:
            from flask_migrate import Migrate
            Migrate(app, db)
        jobs = _init_worker(app)
        _init_views(app)
        app.shell_context_processor(lambda: {
            'db': db, 'redis': app.redis,
            'queue': app.queue, 'jobs': jobs,
            'dump': lambda o: print(dumps(o, indent=2)),
            'user': models[0].query.filter_by(name='chaoyi').first(),
            **{m.__name__: m for m in models},
        })


def _init_models(app):
    from wallet.model.user import User
    from wallet.model.account import Account, AccountType
    from wallet.model.entry import Entry
    from wallet.model.transaction import Transaction, Category
    from wallet.model.enums import Currency, Timezone
    from wallet.model.m1 import M1Portfolio
    from wallet.util.swapsy import init_app as swapsy_init_app, exchange_rate
    models = [
        User, Account, Entry, Transaction, Category,
        Currency, Timezone, AccountType,
        M1Portfolio, exchange_rate,
    ]
    [m.init_app(app) for m in models if hasattr(m, 'init_app')]
    swapsy_init_app(app)
    try:
        from pandas_datareader import DataReader
        from wallet.util.analysis import Analysis
        models += [DataReader, Analysis]
    except ImportError:
        pass
    return models


def _init_worker(app):
    if not app.web or fork() != 0:
        def jobs():
            from rq.registry import BaseRegistry, StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry
            BaseRegistry.get_jobs = lambda s: [app.queue.fetch_job(job_id) for job_id in s.get_job_ids()]
            return {
                'queued': app.queue.get_jobs(),
                'started': StartedJobRegistry(queue=app.queue).get_jobs(),
                'finished': FinishedJobRegistry(queue=app.queue).get_jobs(),
                'failed': FailedJobRegistry(queue=app.queue).get_jobs(),
            }

        return jobs

    from os import _exit
    from rq import Worker
    from rq.job import Job

    class AppJob(Job):
        def _execute(self):
            with app.app_context():
                return super(AppJob, self)._execute()

    Worker(app.queue, connection=app.redis, job_class=AppJob).work()
    _exit(0)


def _init_views(app):
    from flask_graphql import GraphQLView
    from wallet.view.graphql import schema
    from wallet.view.plivo import bp as plivo_bp
    app.add_url_rule('/', endpoint='root', view_func=lambda: app.send_static_file('index.html'))
    app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=app.debug))
    app.register_blueprint(plivo_bp, url_prefix='/plivo')


# monkey-patching SQLAlchemy

class IntEnum(db.TypeDecorator):
    impl = db.Integer

    def __init__(self, enum, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum = enum

    def process_bind_param(self, value, *_):
        return value.value

    def process_result_value(self, value, *_):
        return self.enum(value)


db.utcnow = datetime.utcnow
db.save = lambda e: db.session.add(e) or e
db.IntEnum = IntEnum
