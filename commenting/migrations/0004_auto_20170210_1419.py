# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-02-10 14:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commenting', '0003_auto_20160730_1716'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('document_id',)},
        ),
    ]
