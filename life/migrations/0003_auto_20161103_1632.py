# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-03 16:32
from __future__ import unicode_literals

import db.fields
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0008_documentid_owner'),
        ('life', '0002_auto_20161014_0248'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommonName',
            fields=[
                ('revision', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, serialize=False, to='db.Revision')),
                ('is_tip', models.NullBooleanField()),
                ('is_deleted', models.NullBooleanField()),
                ('name', models.CharField(max_length=255)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='db.DocumentID')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects_revisions', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='lifenode',
            name='commonNames',
            field=db.fields.ManyToManyField(related_name='lifeNode', to='db.DocumentID'),
        ),
        migrations.AlterUniqueTogether(
            name='commonname',
            unique_together=set([('is_tip', 'document')]),
        ),
    ]
