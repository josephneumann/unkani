web: gunicorn manage:app
celery: celery multi start 3 -E -c 3 -A celery_worker.celery --loglevel=info