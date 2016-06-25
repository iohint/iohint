import pytest
import pytz
from datetime import datetime
from unittest.mock import Mock, patch
from cloudwatch.tasks import insert_metric_data, fetch_metric_data, refresh_metric_data
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
                {'Sum': 2002.0, 'Timestamp': datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc), 'Unit': 'Count'}
            ]
        })
        assert inserted_records == 1
        assert duplicate_records == 0
        all_values = Value.objects.all()
        assert len(all_values) == 1
        value = all_values[0]
        assert value.metric_id == metric.id
        assert value.timestamp == datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc)
        assert value.value == 2002

    def test_inserts_multiple_values(self, metric):
        from cloudwatch.models import Value
        inserted_records, duplicate_records = insert_metric_data(metric, {
            'Datapoints': [
                {'Sum': 2005.0, 'Timestamp': datetime(2016, 6, 24, 20, 52, tzinfo=pytz.utc), 'Unit': 'Count'},
                {'Sum': 2002.0, 'Timestamp': datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc), 'Unit': 'Count'},
            ]
        })
        assert inserted_records == 2
        assert duplicate_records == 0
        all_values = Value.objects.all()
        assert len(all_values) == 2

    def test_returns_failed_insert_count(self, metric):
        from cloudwatch.models import Value
        Value.objects.create(metric=metric, timestamp=datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc), value=0)
        inserted_records, duplicate_records = insert_metric_data(metric, {
            'Datapoints': [
                {'Sum': 2005.0, 'Timestamp': datetime(2016, 6, 24, 20, 52, tzinfo=pytz.utc), 'Unit': 'Count'},
                {'Sum': 2002.0, 'Timestamp': datetime(2016, 6, 24, 20, 51, tzinfo=pytz.utc), 'Unit': 'Count'},
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
            region_name='aws-region-1',
            aws_access_key_id='access_key_id',
            aws_secret_access_key='secret_access_key')

    def test_get_metrics_from_cloudwatch(self, mock_metric, mock_boto3):
        cloudwatch = Mock()
        mock_boto3.client.return_value = cloudwatch
        fetch_metric_data(mock_metric, datetime(2015, 1, 1), datetime(2015, 1, 5))
        cloudwatch.get_metric_statistics.assert_called_with(
            Namespace='AWS/ELB',
            MetricName='RequestCount',
            Dimensions=[
                { 'Name': 'LoadBalancerName', 'Value': 'lb-name-1' },
            ],
            StartTime=datetime(2015, 1, 1),
            EndTime=datetime(2015, 1, 5),
            Period=60,
            Statistics=['Sum'],
        )

    def test_returns_metric_data(self, mock_metric, mock_boto3):
        expected_retval = {}
        cloudwatch = Mock()
        cloudwatch.get_metric_statistics.return_value = expected_retval
        mock_boto3.client.return_value = cloudwatch
        actual_retval = fetch_metric_data(mock_metric, datetime(2015, 1, 1), datetime(2015, 1, 5))
        assert actual_retval is expected_retval

@pytest.fixture
def mock_fetch_metric_data(request):
    patcher = patch.object(tasks, 'fetch_metric_data')
    request.addfinalizer(lambda: patcher.stop())
    return patcher.start()

@pytest.fixture
def mock_insert_metric_data(request):
    patcher = patch.object(tasks, 'insert_metric_data')
    request.addfinalizer(lambda: patcher.stop())
    mock = patcher.start()
    mock.return_value = (0, 0)
    return mock

@pytest.fixture
def mock_datetime_now(request):
    patcher = patch.object(tasks, 'datetime')
    request.addfinalizer(lambda: patcher.stop())
    mock = patcher.start()
    mock.now.return_value = datetime(2016, 6, 25, 16, 15, 23)
    mock.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    return mock

@pytest.mark.django_db
class TestRefreshMetricData:
    def test_retrieves_metric(self, metric, mock_fetch_metric_data, mock_insert_metric_data):
        def assert_eager_load(metric, *args):
            assert hasattr(metric, '_load_balancer_cache'), 'load_balancer object should eager loaded before calling fetch_metric_data'
            assert hasattr(metric.load_balancer, '_credential_cache'), 'load_balancer.credential object should eager loaded before calling fetch_metric_data'
        mock_fetch_metric_data.side_effect = assert_eager_load
        refresh_metric_data(metric.id)
        args, kwargs = mock_fetch_metric_data.call_args
        assert args[0].id == metric.id

    def test_begins_loading_past_one_day(self, metric, mock_fetch_metric_data, mock_insert_metric_data, mock_datetime_now):
        refresh_metric_data(metric.id)
        args, kwargs = mock_fetch_metric_data.call_args
        assert args[1] == datetime(2016, 6, 24, 16, 15, 23)
        assert args[2] == datetime(2016, 6, 25, 16, 15, 23)

    def test_inserts_first_data_batch(self, metric, mock_fetch_metric_data, mock_insert_metric_data, mock_datetime_now):
        metric_data = {}
        mock_fetch_metric_data.return_value = metric_data
        refresh_metric_data(metric.id)
        args, kwargs = mock_insert_metric_data.call_args
        assert mock_insert_metric_data.call_count == 1
        assert args[0].id == metric.id
        assert args[1] is metric_data

    def test_queries_back_in_time_if_succeeded(self, metric, mock_fetch_metric_data, mock_insert_metric_data, mock_datetime_now):
        mock_insert_metric_data.side_effect = [
            (1, 0), # 1 inserted, 0 failed
            (0, 0), # 0 inserted, 0 failed; eg nothing found in second query
        ]
        refresh_metric_data(metric.id)
        assert mock_insert_metric_data.call_count == 2

        assert len(mock_fetch_metric_data.call_args_list) == 2
        second_call = mock_fetch_metric_data.call_args_list[1]
        args, kwargs = second_call
        assert args[1] == datetime(2016, 6, 23, 16, 15, 23)
        assert args[2] == datetime(2016, 6, 24, 16, 15, 23)

    def test_doesnot_back_in_time_if_insert_failed(self, metric, mock_fetch_metric_data, mock_insert_metric_data, mock_datetime_now):
        mock_insert_metric_data.return_value = (1, 1) # 1 insert, 1 failed
        refresh_metric_data(metric.id)
        assert mock_insert_metric_data.call_count == 1
