# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-09 15:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property_api', '0006_auto_20161122_0324'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ckanresource',
            name='id',
        ),
        migrations.AddField(
            model_name='ckanresource',
            name='suffix',
            field=models.CharField(default='', max_length=7),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='ckanresource',
            name='slug',
            field=models.CharField(max_length=200, primary_key=True, serialize=False),
        ),
    ]
