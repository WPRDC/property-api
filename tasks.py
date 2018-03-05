from __future__ import absolute_import

import time
from collections import defaultdict

from .models import CKANResource
from .utils import chunks, get_batch_data, carto_intersect, intersect

from wprdc_tools.celery import app
from celery import current_task



def update_progress(task, percent):
    print(task, percent)
    current_task.update_state(state='PROGRESS', meta={'task': task, 'percent': percent})
    


@app.task
def async_data_in_shape(shape, region_name, fields):
    data, failed_searches, all_fields = {}, [], []

    # Set progress to starting - so applications can check on progress
    update_progress('starting', 0)

    # Get list of datasets (CKAN Resources) we're searching through
    resources = CKANResource.objects.filter(resource_id__in=fields.keys())

    # Get IDs of all parcels that are within the shape
    update_progress('Gathering Parcels from Your Region', 10)
    status, pins, geos = intersect(shape, region_name)

    # Setup progress tracking for the data collection setting.
    num_of_resources = len(resources) if len(resources) else 1
    progress_percent = 50 + (30 // num_of_resources)

    # Get data for the parcels
    for resource in resources:
        data[resource.slug] = {}
        success = False
        # Display current percent.  Ticks up for each resource that's been searched through
        update_progress('Gathering {} Data'.format(resource.name), progress_percent)
        progress_percent += (30 // num_of_resources)

        # Iterate of chunks of parcel IDs.  i.e. we'll only work on 15000 Parcel IDs at a time
        for pin_list in chunks(pins, 15000):
            success, temp_data, fieldset = get_batch_data(pin_list, resource,
                                                          fields=fields[str(resource.resource_id)], clean=True)

            data[resource.slug].update(temp_data)

            if success:
                print('pulled {} data'.format(resource.name), time.clock())

                for field in fieldset:
                    if field not in all_fields:
                        all_fields.append(field)

        if not success:
            print('failed search')
            failed_searches.append(resource.name)

    # Pivot data to be per parcel, not resource
    update_progress('Pivoting Data', 90)
    pin_data = defaultdict(dict)
    for resource_key, resource_data in data.items():
        resource = CKANResource.objects.get(pk=resource_key)
        pin_field = resource.parcel_id_field

        for parcel_key, parcel_data in resource_data.items():
            if pin_field in parcel_data:
                del parcel_data[pin_field]

            pin_data[parcel_key][resource_key] = parcel_data

            if 'geo' not in pin_data[parcel_key]:
                pin_data[parcel_key]['geo'] = geos[parcel_key]
    
    print('pivoted data', time.clock())
    print('all_fields: ', all_fields)
    update_progress('Generating Download', 95)
    return pin_data, all_fields
