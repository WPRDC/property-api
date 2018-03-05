import requests
import json
import psycopg2
import copy
import time

from bs4 import BeautifulSoup


from .settings import API_URL
from .models import CKANResource

from collections import defaultdict, Counter, OrderedDict as OD

QUERY_TEMPLATE = 'SELECT * FROM "{}" WHERE "{}" = \'{}\';'
QUERY_TEMPLATE_MULTI = 'SELECT {} FROM "{}" WHERE "{}" IN ({});'


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_data(pin, resource):
    qry = QUERY_TEMPLATE.format(resource.resource_id, resource.parcel_id_field, pin)
    r = requests.get(API_URL, params={'sql': qry})
    if r.status_code == 200:
        rcds = r.json()['result']['records']
        if rcds:
            return True, cleanup(r.json()['result']['records'])
        else:
            return True, []
    else:
        return False, []


def get_batch_data(pins, resource, fields=[], clean=True):
    result = {}
    # Set fields.  Either a comma separated list of parcel_id_field and then other field IDs...
    if fields:
        fields_str = '"{}","'.format(resource.parcel_id_field) + '","'.join(fields) + '"'
    # Or simply all fields
    else:
        fields_str = '*'

    # copy fields to work on them.
    fieldset = copy.deepcopy(fields)

    # convert list of pins to comma separated string list
    pin_list = "'{}'".format("','".join(pins))

    # Build query and send it to CKAN instance
    qry = QUERY_TEMPLATE_MULTI.format(fields_str, str(resource.resource_id), resource.parcel_id_field, pin_list)
    r = requests.post(API_URL, json={'sql': qry})

    if r.status_code == 200:
        # Instantiate counter for keeping track of records per parcel
        counter = Counter()

        # Get the returned data
        data = r.json()['result']['records']

        for row in data:
            # Extract parcel ID, and remove that record from the data
            pin = row[resource.parcel_id_field]
            del row[resource.parcel_id_field]

            if pin in result:
                counter[pin] += 1
                row = {k + "_" + str(counter[pin]): v for k, v in row.items()}
                result[pin].update(cleanup(row))
                # update set of fields`
                for field in row.keys():
                    if field not in fieldset:
                        fieldset.append(field)
            else:
                result[pin] = cleanup(row) if clean else row

        return True, result, fieldset

    else:
        return False, {}, fieldset


def cleanup(data):
    try:    
        #del data['_full_text']
        for record in data:
            if "_full_text" in record:
                del record['_full_text']
    finally:
        return data

def carto_intersect(shape, shape_table=None, parcel_table='property_assessment_app'):
    query_template = 'SELECT the_geom, parid FROM {parcel_table} a WHERE ST_INTERSECTS({shape}, a.the_geom)'
    url = 'https://wprdc.carto.com/api/v2/sql'
    data = {'skipfields': ','.join(['cartodb_id', 'created_at', 'updated_at', 'name', 'description']),
            'format': 'geojson',
            'q': query_template.format(parcel_table=parcel_table, shape=shape)}

    resp = requests.get(url, params=data)
    pins, geos = [], {}
    if resp.status_code != 200:
        pins = []
    else:
        for feature in resp.json()['features']:
            pin = feature['properties']['parid']
            if pin:
                pins.append(pin)
                geos[pin] = feature['geometry']

    return resp.status_code, pins, geos

def intersect(shape, region_name, shape_table=None, parcel_table='parcel_boundaries'):
    if region_name:
        qry = 'SELECT pin, ST_AsGeoJSON(geom) as the_geom FROM {parcel_table} a WHERE ST_INTERSECTS({shape}, a.geom)'

    shape = shape.replace('the_geom', 'geom')
    query_template = 'SELECT pin, ST_AsGeoJSON(geom) as the_geom FROM {parcel_table} a WHERE ST_INTERSECTS({shape}, a.geom)'
    qry = query_template.format(parcel_table=parcel_table, shape=shape)

    conn = psycopg2.connect("dbname=geo")
    cur = conn.cursor()

    cur.execute(qry)
    rows = cur.fetchall()

    pins, geos = [],{}

    for row in rows:
        if row[0]:
            pins.append(row[0])
            
            geos[row[0]] = json.loads(row[1])

    cur.close()
    conn.close()

    return True, pins, geos



def to_geojson(data, fields):
    geo_dict = {'type': 'FeatureCollection',
                'features': []}

    for k, v in data.items():
        props = {"PIN": k}
        for r, d in v.items():
            if r == 'geo':
                continue
            resource = CKANResource.objects.get(pk=r)
            suffix = "__" + resource.suffix
            d = {k + suffix: v for k, v in d.items()}

            props.update(d)

        feature = {
            "type": 'Feature',
            "geometry": v['geo'],
            "properties": props
        }
        geo_dict['features'].append(feature)

    return geo_dict


def to_csv(data, fields):
    rows, new_fields = [], []
    # FOR EACH PARCEL
    suffixes = {}
    for resource in CKANResource.objects.all():
        suffixes[resource.slug] = resource.suffix

    for pin, values in data.items():
        row = {"PIN": pin, "geom": values['geo']}

        # FOR EACH RESOURCE
        for resource, datum in values.items():
            if resource == 'geo':
                continue
            else:
                suffix = "__" + suffixes[resource]
                new_data = {}
                for field in fields:
                    if field in datum.keys():
                        new_data[field+suffix] = datum[field]
                        if field + suffix not in new_fields:
                            new_fields.append(field + suffix)
                row.update(new_data)

        rows.append(row)

    return rows, new_fields


def data_in_shape(shape, fields):
    print('start', time.clock())
    data, failed_searches = {}, []
    resources = CKANResource.objects.filter(resource_id__in=fields.keys())
    all_fields = []

    # Get PINs
    status, pins, geos = intersect(shape)

    # Get data for the parcels
    for resource in resources:
        data[resource.slug] = {}
        success = False
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
            failed_searches.append(resource.name)

    # Pivot data to be per parcel, not resource
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

    return pin_data, all_fields
    
def pivot_resource_to_parcel(data):
    # Pivot data to be per parcel, not resource
    pin_data = defaultdict(dict)

    for resource_id, resource_data in data.items():
        resource = CKANResource.objects.get(pk=resource_id)
        pin_field = resource.parcel_id_field


        for parcel_id, parcel_data in resource_data.items():
            # remove parcel id field from data since it will be redundant
            if pin_field in parcel_data:
                del parcel_data[pin_field]

            pin_data[parcel_id][resource_id] = parcel_data

            if 'geo' not in pin_data[parcel_id] and resource.has_geo:
                if type(parcel_data) == list:
                    pin_data[parcel_id]['geos'] = {'centroid':
                                                       {'type': 'Point',
                                                        'coordinates': [
                                                            parcel_data[0][resource.lon_field],
                                                            parcel_data[0][resource.lat_field]]
                                                        }
                                                   }
                elif type(parcel_data) == dict:
                    pin_data[parcel_id]['geos'] = {'centroid':
                                                       {'type': 'Point',
                                                        'coordinates': [
                                                            parcel_data[resource.lon_field],
                                                            parcel_data[resource.lat_field]]
                                                        }
                                                   }
    return pin_data

def get_parcels(parcel_ids, resources):
    data = {}
    failed_searches = []

    for resource in resources:
        success, data[resource.slug], fields = v1_get_batch_data(parcel_ids, resource)
        if not success:
            failed_searches.append(resource.name)

    pin_data = pivot_resource_to_parcel(data)

    results = []
    for pin, data in pin_data.items():
        r = OD([('parcel_id', pin)])
        if 'geos' in data:
            r['geos'] = data['geos']
            del data['geos']

        # cleanup CKAN-specific fields
        for k, v in data.items():
            if type(v) == list:
                for row in v:
                    del row['_full_text']
                    del row['_id']

            elif type(v) == dict:
                del v['_full_text']
                del v['_id']
                
        # fill in missing keys
        for resource in resources:
            if resource.slug not in data:
                data[resource.slug] = []

        r['owner'] = get_owner_name(pin)
        r['data'] = data
        results.append(r)
    return results, failed_searches

    
def v1_get_batch_data(pins, resource, fields=[], clean=True):
    result = {}
    if fields:
        fields_str = '"{}","'.format(resource.parcel_id_field) + '","'.join(fields) + '"'
    else:
        fields_str = '*'

    fieldset = copy.deepcopy(fields)
    pin_list = "'{}'".format("','".join(pins))
    qry = QUERY_TEMPLATE_MULTI.format(fields_str, resource.resource_id, resource.parcel_id_field, pin_list)

    r = requests.post(API_URL, json={'sql': qry})

    if r.status_code == 200:
        data = json.loads(r.text)['result']['records']
        for row in data:
            pin = row[resource.parcel_id_field]
            del row[resource.parcel_id_field]
            if pin not in result:
                result[pin] = [cleanup(row)] if clean else [row]
            else:
                result[pin].append(cleanup(row) if clean else row)
            for field in row.keys():
                if field not in fieldset:
                    fieldset.append(field)

        return True, result, fieldset

    else:
        return False, {}, fieldset

    
    
def get_owner_name(parcel_id):
    URL_TEMPLATE = 'http://www2.county.allegheny.pa.us/RealEstate/GeneralInfo.aspx?ParcelID='
    owner_name = ''
    r = requests.get(URL_TEMPLATE+parcel_id);
    try:
        if (r.ok):
            soup = BeautifulSoup(r.text, 'html.parser')
            thing = soup.find_all(id='BasicInfo1_lblOwner')
            owner_name = ' '.join(thing[0].text.split())

    finally:
        return owner_name
