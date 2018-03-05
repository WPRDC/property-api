from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.conf import settings

import time
import json
import csv
from collections import OrderedDict as OD, defaultdict

from .models import CKANResource
from .utils import get_data, get_batch_data, carto_intersect, to_geojson, to_csv, data_in_shape, get_parcels, \
    get_owner_name

from .tasks import async_data_in_shape

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

DATATYPES = ['json', 'geojson', 'csv', 'carto']


def index(request):
    return render(request, 'index.html')

@cache_page(CACHE_TTL)
def single(request):
    try:
        pin = request.GET['parcel_id']
    except KeyError:
        return JsonResponse({'success': False, 'help': 'parcel_id required'}, status=400)

    resources = CKANResource.objects.all()
    failed_searches = []
    data = {}
    geo = {}

    for resource in resources:
        success, data[resource.slug] = get_data(pin, resource)
        if not success:
            failed_searches.append(resource.name)
        if success and resource.has_geo:
            try:
                geo = {'latitude': data[resource.slug][0][resource.lat_field],
                       'longitude': data[resource.slug][0][resource.lon_field]}
            except:
                geo = {'latitude': '', 'longitude': ''}

    response = OD(
        [('success', True),
         ('help', 'Data for parcel {}.'.format(pin)),
         ('geo', geo),
         ('owner', get_owner_name(pin)),
         ('results', data),
         ('failed_searches', failed_searches), ]
    )

    return JsonResponse(response)

@cache_page(CACHE_TTL)
def single_parcel(request, pin=""):
    if not pin:
        return JsonResponse({'success': False, 'help': 'parcel_id required'}, status=400)

    resources = CKANResource.objects.all()
    failed_searches = []
    data = {}
    geo = {}

    for resource in resources:
        success, data[resource.slug] = get_data(pin, resource)
        if not success:
            failed_searches.append(resource.name)
        if success and resource.has_geo:
            geo = {
                'centroid': {
                    'type': 'Point',
                    'coordinates': [data[resource.slug][0][resource.lon_field],
                                    data[resource.slug][0][resource.lat_field]]
                },
                'boundary': {}
            }

    response = OD(
        [('success', True),
         ('help', 'Data for parcel {}.'.format(pin)),
         ('geo', geo),
         ('owner', get_owner_name(pin)),
         ('data', data),
         ('failed_searches', failed_searches), ]
    )

    return JsonResponse(response)


def batch(request):
    try:
        pins = request.GET['parcel_ids']
    except KeyError:
        return JsonResponse({'success': False, 'help': 'parcel_ids required'}, status=400)

    resources = CKANResource.objects.all()
    failed_searches, data, geo = [], {}, {}
    pins = pins.split(',')

    for resource in resources:
        success, data[resource.slug] = get_batch_data(pins, resource)
        if not success:
            failed_searches.append(resource.name)

    response = OD(
        [('success', True),
         ('help', 'Data for parcel {}.'.format(pins)),
         ('geo', geo),
         ('results', data),
         ('failed_searches', failed_searches), ]
    )

    return JsonResponse(response)


def within(request):
    try:
        shape = request.GET['shape']
    except KeyError:
        return JsonResponse({'success': False, 'help': 'must shape of region you want to search in'})

    status, pins = carto_intersect(shape)
    response = {'success': True, 'help': '', 'pins': pins}

    if response != 200:
        response['success'] = False
        response['help'] = 'call to carto failed'

    return JsonResponse(response, status=status)


def address_search(request):
    try:
        num = request.GET['number']
        street = request.GET['street']
        city = request.GET['city']
        zip = request.GET['zip']
    except KeyError:
        return JsonResponse({'success': False, 'help': 'must submit street number, street name, city and zip code'},
                            status=400)


@csrf_exempt
def data_within(request):
    # Get shape from request, if not return error
    try:
        shape = request.POST['shape']
    except KeyError:
        return JsonResponse({'success': False, 'help': 'must provide shape of region within which to you want to search'}, status=400)
    try:
        region_name = request.POST['region_name']
    except:
        region_name = None
    # Get fields from request and convert to dict keyed by resource
    fields = {}
    if 'fields' in request.POST:
        fs = json.loads(request.POST['fields'])
        for f in fs:
            if f['r'] in fields:
                fields[f['r']].append(f['f'])
            else:
                fields[f['r']] = [f['f']]

    # data, fields_set = async_data_in_shape(shape, fields)
    getter = async_data_in_shape.delay(shape, region_name, fields)
    # data, fields_set = getter.get()
    return JsonResponse({'job_id': getter.id})


def get_collected_data(request):

    if 'job' in request.GET:
        job_id = request.GET['job']
    else:
        return HttpResponse('No job id given.', status=400)

    # Get data type
    if 'type' not in request.GET:
        datatype = 'json'
    else:
        datatype = request.GET['type']

    if datatype not in DATATYPES:
        return JsonResponse({'success': False, 'help': datatype + ' is not a valid datatype'}, status=400)

    job = async_data_in_shape.AsyncResult(job_id)
    if job.ready():
        data, fields_set = job.get()
    else:
        return HttpResponse('Job not ready.', status=400)

    if datatype == 'json':
        response = {'success': True, 'help': '', 'data': data}
        return JsonResponse(response, status=200)

    elif datatype == 'geojson':
        data = to_geojson(data, fields_set)
        response = HttpResponse(content_type='text/json')
        response['Content-Disposition'] = 'attachment; filename="parcel_data.geojson"'
        json.dump(data, response)
        return response

    elif datatype == 'csv':
        print('making csv', time.clock())
        data, new_fields = to_csv(data, fields_set)
        print('made csv', time.clock())
        fields_set = ['PIN', 'geom'] + new_fields
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="parcel_data.csv"'
        dwriter = csv.DictWriter(response, fieldnames=fields_set)
        dwriter.writeheader()
        dwriter.writerows(data)
        print('done', time.clock())
        return response


def get_progress(request):
    """ A view to report the progress to the user """
    if 'job' in request.GET:
        job_id = request.GET['job']
    else:
        return HttpResponse('No job id given.')

    job = async_data_in_shape.AsyncResult(job_id)

    if job.state == "PROGRESS":
        data = job.result
    elif job.state == "SUCCESS":
        data = {'task': 'Complete', 'percent': 100}
    else:
        data = {'task': 'Starting', 'percent': 0}

    return JsonResponse(data)


############
##  BETA  ##
###############################################################################
@cache_page(CACHE_TTL)
def beta_parcels(request, parcel_ids=None):
    resources = CKANResource.objects.all()
    failed_searches, data, geo = [], {}, {}
    response = OD(
        [('success', False),
         ('help', 'Data for parcels'),
         ('results', []),
         ('failed_searches', failed_searches), ]
    )

    if parcel_ids:
        pins = parcel_ids.split(',')
        results, failed_searches = get_parcels(pins, resources)

        response['success'] = True
        response['results'] = results
        response['failed_searches'] = failed_searches

        return JsonResponse(response)
    else:
        response['help'] = 'No parcel IDs Provided'
        pass
