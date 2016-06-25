from datetime import timedelta
import os

BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://')
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'iohint.background.tasks.add',
        'schedule': timedelta(seconds=30),
        'args': (16, 16)
    },
}
