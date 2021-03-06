# -*- coding: utf-8 -*-
# Generated by Django 1.10b1 on 2016-06-25 15:52
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Credential',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('access_key_id', models.CharField(max_length=20)),
                ('secret_access_key', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='LoadBalancer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('region', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=32)),
                ('credential', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cloudwatch.Credential')),
            ],
        ),
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('statistic', models.CharField(max_length=10)),
                ('load_balancer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cloudwatch.LoadBalancer')),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('value', models.FloatField()),
                ('metric', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cloudwatch.Metric')),
            ],
        ),
        migrations.AddField(
            model_name='loadbalancer',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cloudwatch.Service'),
        ),
        migrations.AlterUniqueTogether(
            name='value',
            unique_together=set([('metric', 'timestamp')]),
        ),
        migrations.AlterUniqueTogether(
            name='service',
            unique_together=set([('owner', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='metric',
            unique_together=set([('load_balancer', 'name', 'statistic')]),
        ),
        migrations.AlterUniqueTogether(
            name='loadbalancer',
            unique_together=set([('service', 'region', 'name')]),
        ),
    ]
