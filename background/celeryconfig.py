from datetime import timedelta
import os

BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://')
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_IMPORTS = ('tasks', )

CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'tasks.add',
        'schedule': timedelta(seconds=1),
        'args': (16, 16)
    },
}
