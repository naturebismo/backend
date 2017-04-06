# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-03-12 14:44
from __future__ import unicode_literals

from django.db import migrations, models


def set_revision_document_id_and_index(apps, schema_editor):
    from db.models import Revision
    for revision in Revision.objects.all():
        revision.index = Revision.objects.filter(
            document_id=revision.document_id,
            id__lt=revision.id
        ).count() + 1
        revision.save()


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0009_documentid_privacy'),
    ]

    operations = [
        migrations.AddField(
            model_name='revision',
            name='revision_document_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='revision',
            name='index',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(set_revision_document_id_and_index),
    ]
