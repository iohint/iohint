import datetime
import pytest
import pytz
from unittest.mock import Mock, patch
from cloudwatch.tasks import insert_metric_data, fetch_metric_data
from cloudwatch import tasks

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

@pytest.fixture
def mock_credential():
    return Mock(access_key_id='access_key_id', secret_access_key='secret_access_key')

@pytest.fixture
def mock_load_balancer(mock_credential):
    retval = Mock(region='aws-region-1', credential=mock_credential)
    retval.name = 'lb-name-1'
    return retval

@pytest.fixture
def mock_metric(mock_load_balancer):
    retval = Mock(load_balancer=mock_load_balancer, statistic='Sum')
    retval.name = 'RequestCount'
    return retval

@pytest.mark.django_db
class TestInsertMetricData:
    def test_return_values_zero(self, metric):
        inserted_records, duplicate_records = insert_metric_data(metric, { 'Datapoints': [] })
        assert inserted_records == 0
        assert duplicate_records == 0

    def test_inserts_single_value(self, metric):
        from cloudwatch.models import Value
        inserted_records, duplicate_records = insert_metric_data(metric, {
            'Datapoints': [
                {'Sum': 2002.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 51), 'Unit': 'Count'}
            ]
        })
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
        inserted_records, duplicate_records = insert_metric_data(metric, {
            'Datapoints': [
                {'Sum': 2005.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 52), 'Unit': 'Count'},
                {'Sum': 2002.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 51), 'Unit': 'Count'},
            ]
        })
        assert inserted_records == 2
        assert duplicate_records == 0
        all_values = Value.objects.all()
        assert len(all_values) == 2

    def test_returns_failed_insert_count(self, metric):
        from cloudwatch.models import Value
        Value.objects.create(metric=metric, timestamp=datetime.datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc), value=0)
        inserted_records, duplicate_records = insert_metric_data(metric, {
            'Datapoints': [
                {'Sum': 2005.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 52), 'Unit': 'Count'},
                {'Sum': 2002.0, 'Timestamp': datetime.datetime(2016, 6, 24, 20, 51), 'Unit': 'Count'},
            ]
        })
        assert inserted_records == 1
        assert duplicate_records == 1
        all_values = Value.objects.all()
        assert len(all_values) == 2

@pytest.fixture
def mock_boto3(request):
    patcher = patch.object(tasks, 'boto3')
    request.addfinalizer(lambda: patcher.stop())
    return patcher.start()

class TestFetchMetricData:
    def test_connects_to_cloudwatch(self, mock_metric, mock_boto3):
        fetch_metric_data(mock_metric, '1', '2')
        mock_boto3.client.assert_called_with('cloudwatch',
            region='aws-region-1',
            aws_access_key_id='access_key_id',
            aws_secret_access_key='secret_access_key')

    def test_get_metrics_from_cloudwatch(self, mock_metric, mock_boto3):
        cloudwatch = Mock()
        mock_boto3.client.return_value = cloudwatch
        fetch_metric_data(mock_metric, datetime.datetime(2015, 1, 1), datetime.datetime(2015, 1, 5))
        cloudwatch.get_metric_statistics.assert_called_with(
            Namespace='AWS/ELB',
            MetricName='RequestCount',
            Dimensions=[
                { 'Name': 'LoadBalancerName', 'Value': 'lb-name-1' },
            ],
            StartTime=datetime.datetime(2015, 1, 1),
            EndTime=datetime.datetime(2015, 1, 5),
            Period=60,
            Statistics=['Sum'],
        )

    def test_returns_metric_data(self, mock_metric, mock_boto3):
        expected_retval = {}
        cloudwatch = Mock()
        cloudwatch.get_metric_statistics.return_value = expected_retval
        mock_boto3.client.return_value = cloudwatch
        actual_retval = fetch_metric_data(mock_metric, datetime.datetime(2015, 1, 1), datetime.datetime(2015, 1, 5))
        assert actual_retval is expected_retval
