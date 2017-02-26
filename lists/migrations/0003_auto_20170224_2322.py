# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-02-24 23:22
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0002_auto_20170224_2320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='list',
            name='description',
            field=models.CharField(blank=True, default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='list',
            name='items',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]