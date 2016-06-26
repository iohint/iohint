import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'iohint.settings'

import django
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from cloudwatch.models import Service, Credential, LoadBalancer, Metric

def get_profile_credentials(profile_name):
    from configparser import ConfigParser
    from configparser import ParsingError
    from configparser import NoOptionError
    from configparser import NoSectionError
    from os import path
    config = ConfigParser()
    config.read([path.join(path.expanduser("~"),'.aws/credentials')])
    try:
        aws_access_key_id = config.get(profile_name, 'aws_access_key_id')
        aws_secret_access_key = config.get(profile_name, 'aws_secret_access_key')
    except ParsingError:
        print('Error parsing config file')
        raise
    except (NoSectionError, NoOptionError):
       try:
           aws_access_key_id = config.get('default', 'aws_access_key_id')
           aws_secret_access_key = config.get('default', 'aws_secret_access_key')
       except (NoSectionError, NoOptionError):
           print('Unable to find valid AWS credentials')
           raise
    return aws_access_key_id, aws_secret_access_key

@transaction.atomic
def create_test_data():
    admin = User.objects.create_superuser(username='admin', password='123', email='')
    service = Service.objects.create(owner=admin, name='na3 dws')
    aws_access_key_id, aws_secret_access_key = get_profile_credentials('replicon-production')
    cred = Credential.objects.create(access_key_id=aws_access_key_id, secret_access_key=aws_secret_access_key)
    lb = LoadBalancer.objects.create(service=service, region='us-west-2', name='na3-dws-int', credential=cred)
    Metric.objects.create(load_balancer=lb, name='RequestCount', statistic='Sum')

create_test_data()
