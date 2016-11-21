web: gunicorn manage:app
celeryworker: celery worker -A celery_worker.celery --loglevel=info