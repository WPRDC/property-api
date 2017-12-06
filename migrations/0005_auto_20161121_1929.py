# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-22 00:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property_api', '0004_auto_20161121_1928'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ckanresource',
            name='contains_geo',
        ),
        migrations.AddField(
            model_name='ckanresource',
            name='has_geo',
            field=models.BooleanField(default=False, help_text='Should only be for one resource.', verbose_name='Contains coordinates'),
            preserve_default=False,
        ),
    ]