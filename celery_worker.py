#!./venv/bin/python3
import sys, subprocess, os, click
from celery import Celery
from flask import Flask


def make_celery(app):
    celery = Celery(__name__, broker=os.environ.get('CELERY_BROKER_URL', 'redis://'),
                    backend=os.environ.get('CELERY_BROKER_URL', 'redis://'))
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)

celery = make_celery(flask_app)
