import datetime
import pytest
import pytz
from cloudwatch.tasks import insert_metric_data

@pytest.fixture
def user():
    from django.contrib.auth.models import User
    return User.objects.create_superuser(username='admin', password='123', email='')

@pytest.fixture
def service(user):
    from cloudwatch.models import Service
    return Service.objects.create(owner=user, name='na3 dws')

@pytest.fixture
def credential():
    from cloudwatch.models import Credential
    return Credential.objects.create(access_key_id='access_key_id', secret_access_key='secret_access_key')

@pytest.fixture
def load_balancer(service, credential):
    from cloudwatch.models import LoadBalancer
    return LoadBalancer.objects.create(service=service, region='aws-region-1', name='lb-name-1', credential=credential)

@pytest.fixture
def metric(load_balancer):
    from cloudwatch.models import Metric
    return Metric.objects.create(load_balancer=load_balancer, name='RequestCount', statistic='Sum')

@pytest.mark.django_db
class TestInsertMetricData:
    def test_return_values_zero(self, metric):
        inserted_records, duplicate_records = insert_metric_data(metric, [])
        assert inserted_records == 0
        assert duplicate_records == 0

    def test_inserts_single_value(self, metric):
        from cloudwatch.models import Value
        inserted_records, duplicate_records = insert_metric_data(metric, [
            {'Sum': 2002.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 51), 'Unit': 'Count'}
        ])
        assert inserted_records == 1
        assert duplicate_records == 0
        all_values = Value.objects.all()
        assert len(all_values) == 1
        value = all_values[0]
        assert value.metric_id == metric.id
        assert value.timestamp == datetime.datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc)
        assert value.value == 2002

    def test_inserts_multiple_values(self, metric):
        from cloudwatch.models import Value
        inserted_records, duplicate_records = insert_metric_data(metric, [
            {'Sum': 2005.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 52), 'Unit': 'Count'},
            {'Sum': 2002.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 51), 'Unit': 'Count'},
        ])
        assert inserted_records == 2
        assert duplicate_records == 0
        all_values = Value.objects.all()
        assert len(all_values) == 2

    def test_returns_failed_insert_count(self, metric):
        from cloudwatch.models import Value
        Value.objects.create(metric=metric, timestamp=datetime.datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc), value=0)
        inserted_records, duplicate_records = insert_metric_data(metric, [
            {'Sum': 2005.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 52), 'Unit': 'Count'},
            {'Sum': 2002.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 51), 'Unit': 'Count'},
        ])
        assert inserted_records == 1
        assert duplicate_records == 1
        all_values = Value.objects.all()
        assert len(all_values) == 2
