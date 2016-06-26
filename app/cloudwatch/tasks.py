from celery import shared_task
from django.db import transaction, IntegrityError
from .models import Value, Metric, LoadBalancer
from datetime import datetime, timedelta
import pytz
import boto3

# dispatch tasks to refresh the CloudWatch data for every ELB
@shared_task
def schedule_all_elb_refreshes():
    for elb in LoadBalancer.objects.all():
        refresh_elb_metrics.delay(str(elb.id))

# Refresh all metrics for a given load balancer; all the metrics will be refreshed in-process, since
# (a) can't figure out how to make celery take a task w/ a list and execute multiple subtasks without waiting
# on it in-process, and (b) doesn't seem like a big deal to be able to scale a handful of metrics out, anyway.
@shared_task
def refresh_elb_metrics(elb_id):
    elb = LoadBalancer.objects.get(pk=elb_id)
    for metric in elb.metric_set.all():
        refresh_metric_data(str(metric.id))

# Refresh a single metric; multiple calls to CloudWatch will be made until we have retrieved all available
# data for this metric and stored it in our database.
@shared_task
@transaction.atomic
def refresh_metric_data(metric_id):
    metric = Metric.objects.select_related('load_balancer', 'load_balancer__credential').get(pk=metric_id)
    query_end = datetime.now()
    while True:
        query_start = query_end - timedelta(seconds=60  * 1440)
        metric_data = fetch_metric_data(metric, query_start, query_end)
        insert_count, failed_count = insert_metric_data(metric, metric_data)
        if insert_count == 0 or failed_count > 0:
            break
        query_end = query_start

def fetch_metric_data(metric, query_start, query_end):
    load_balancer = metric.load_balancer
    credential = load_balancer.credential
    cloudwatch = boto3.client('cloudwatch',
        region_name=load_balancer.region,
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

def insert_metric_data(metric, metric_statistics):
    import datetime
    insert_count = 0;
    failed_count = 0
    for stat in metric_statistics['Datapoints']:
        try:
            with transaction.atomic(): # allows outer transaction to proceed despite potential for error
                Value.objects.create(metric=metric, timestamp=stat['Timestamp'], value=stat['Sum'])
            insert_count += 1
        except IntegrityError:
            failed_count += 1
    return (insert_count, failed_count)
