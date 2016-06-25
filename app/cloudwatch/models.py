from django.conf import settings
from django.db import models

import uuid

# Create your models here.

# organization  HAS MANY  users
# organization  HAS MANY  projects
# project  HAS MANY   services
# organization  HAS MANY  credentials

# ELB
#   -> credential
#   -> metric
#     -> value

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.TextField()

    class Meta:
        unique_together = [ ('owner', 'name') ]

class Credential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    access_key_id = models.CharField(max_length=20)
    secret_access_key = models.CharField(max_length=40)

class LoadBalancer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service)
    region = models.CharField(max_length=20)
    name = models.CharField(max_length=32)
    credential = models.ForeignKey(Credential)

    class Meta:
        unique_together = [ ('service', 'region', 'name') ]

class Metric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    load_balancer = models.ForeignKey(LoadBalancer)
    name = models.CharField(max_length=50)
    statistic = models.CharField(max_length=10)

    class Meta:
        unique_together = [ ('load_balancer', 'name', 'statistic') ]

class Value(models.Model):
    metric = models.ForeignKey(Metric)
    timestamp = models.DateTimeField()
    value = models.FloatField()

    class Meta:
        unique_together = [ ('metric', 'timestamp') ]
