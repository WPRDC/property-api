from django.db import models
from .settings import CKAN_ROOT


class CKANResource(models.Model):
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, primary_key=True)
    suffix = models.CharField(max_length=7)
    resource_id = models.CharField('Resource ID', max_length=40, default=None)
    parcel_id_field = models.CharField('Parcel ID field (e.g. PARID)', max_length=200)
    multi_per_pin = models.BooleanField('Parcel can have multiple records')
    info = models.CharField(max_length=400)
    has_geo = models.BooleanField('Contains coordinates', help_text='Should only be for one resource.')
    lat_field = models.CharField(max_length=20, help_text='Only if field contains coordinates', blank=True)
    lon_field = models.CharField(max_length=20, help_text='Only if field contains coordinates', blank=True)

    def __str__(self):
        return self.name

    class Meta():
        verbose_name = 'CKAN Resource'
