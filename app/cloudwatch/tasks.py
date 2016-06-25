from celery import shared_task
from django.db import transaction, IntegrityError
from .models import Value
import pytz

@shared_task
def add(x, y):
    return x + y

@shared_task
def mul(x, y):
    return x * y


# Task #1: dispatch tasks to refresh the CloudWatch data for every ELB

# Task #2: Refresh the CloudWatch data for a specific ELB
#   Reads CloudWatch data until we find an overlap with data we already have.

# @transaction.atomic FIXME TDD
@shared_task
def pull_metric_data(metric_id):
    # retrieve metric, lb, cred
    # boto connect_to_region
    # loop over query time
    #   get_metric_statistics
    #   insert results into value; count integrity errors & inserted records
    pass

# sub-method: insert results & return duplicate count, insert count
def insert_metric_data(metric, metric_statistics):
    import datetime
    insert_count = 0;
    failed_count = 0
    for stat in metric_statistics:
        try:
            with transaction.atomic(): # allows outer transaction to proceed despite potential for error
                Value.objects.create(metric=metric, timestamp=pytz.utc.localize(stat['Timestamp']), value=stat['Sum'])
            insert_count += 1
        except IntegrityError:
            failed_count += 1
    return (insert_count, failed_count)
