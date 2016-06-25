from celery import shared_task
from django.db import transaction, IntegrityError
from .models import Value
import pytz
import boto3

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
def refresh_metric_data(metric_id):
    # retrieve metric, lb, cred
    # boto connect_to_region
    # loop over query time
    #   get_metric_statistics
    #   insert results into value; count integrity errors & inserted records
    pass

def fetch_metric_data(metric, query_start, query_end):
    load_balancer = metric.load_balancer
    credential = load_balancer.credential
    cloudwatch = boto3.client('cloudwatch',
        region=load_balancer.region,
        aws_access_key_id=credential.access_key_id,
        aws_secret_access_key=credential.secret_access_key)
    return cloudwatch.get_metric_statistics(
        Namespace='AWS/ELB',
        MetricName=metric.name,
        Dimensions=[
            { 'Name': 'LoadBalancerName', 'Value': load_balancer.name },
        ],
        StartTime=query_start,
        EndTime=query_end,
        Period=60,
        Statistics=[ metric.statistic ],
    )

# sub-method: insert results & return duplicate count, insert count
def insert_metric_data(metric, metric_statistics):
    import datetime
    insert_count = 0;
    failed_count = 0
    for stat in metric_statistics['Datapoints']:
        try:
            with transaction.atomic(): # allows outer transaction to proceed despite potential for error
                Value.objects.create(metric=metric, timestamp=pytz.utc.localize(stat['Timestamp']), value=stat['Sum'])
            insert_count += 1
        except IntegrityError:
            failed_count += 1
    return (insert_count, failed_count)
