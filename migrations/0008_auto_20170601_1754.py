# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-06-01 17:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property_api', '0007_auto_20170209_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ckanresource',
            name='resource_id',
            field=models.CharField(default=None, max_length=40, verbose_name='Resource ID'),
        ),
    ]
