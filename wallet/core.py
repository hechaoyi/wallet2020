from datetime import datetime
from logging import INFO
from os import environ, fork, path

from flask import Flask
from flask.json import dumps
from flask_graphql import GraphQLView
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from redis import from_url
from rq import Queue

db = SQLAlchemy()
db.utcnow = datetime.utcnow


def create_app():
    app = Flask(__name__,
                static_url_path='',
                static_folder=path.abspath(path.dirname(__file__) + '/../ui/build'))
    _init_configurations(app)
    _init_components(app)
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


def _init_components(app):
    db.init_app(app)
    Migrate(app, db)
    if 'REDIS_URL' in environ:
        app.redis = from_url(environ['REDIS_URL'])
        app.queue = Queue(connection=app.redis)
    jobs = _init_worker(app)

    # models
    from wallet.model.m1 import M1Portfolio
    models = [
        M1Portfolio,
    ]
    [m.init_app(app) for m in models if hasattr(m, 'init_app')]

    # views
    from wallet.view.graphql import schema
    from wallet.view.plivo import bp as plivo_bp
    app.add_url_rule('/', endpoint='root', view_func=lambda: app.send_static_file('index.html'))
    app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=app.debug))
    app.register_blueprint(plivo_bp, url_prefix='/plivo')

    # cli
    from wallet.util.swapsy import init_app as swapsy_init_app
    swapsy_init_app(app)
    app.shell_context_processor(lambda: {
        'db': db,
        'redis': app.redis,
        'queue': app.queue,
        'jobs': jobs,
        'dump': lambda o: print(dumps(o, indent=2)),
        **{m.__name__: m for m in models},
    })


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
