import csv
import os
import re

import utm
from elasticsearch import Elasticsearch
from elasticsearch import NotFoundError
from elasticsearch.client import IndicesClient
from lib.classificator import Classifier


INDEX = 'thc'
DOC_TYPE = 'marker'


def find_years(text):
    try:
        matches = re.findall(r"\d{4}", text)
        return [int(m) for m in matches]
    except TypeError:
        return []


def get_data(path='data/Historical Marker_20150521_145030_254.csv'):
    with open(path, 'r') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            text = row['markertext']
            years = find_years(text)
            row['address'] = row['address'].strip()

            # add our own data
            row['years'] = years
            row['classifications'] = Classifier(years, text=text).classify()
            try:
                lat, lon = utm.to_latlon(
                    int(row['utm_east']),
                    int(row['utm_north']),
                    int(row['utm_zone']),
                    northern=True,
                )
                row['location'] = {
                    "lat": lat,
                    "lon": lon,
                }
            except ValueError:
                # log warn missing
                pass
            yield row


def set_mapping():
    """
    http://localhost:9200/thc/marker/_mapping?pretty
    """
    host = os.environ.get('ELASTICSEARCH_HOST', 'localhost')
    connection = Elasticsearch([host])
    iclient = IndicesClient(connection)
    try:
        iclient.delete(index=[INDEX])
    except NotFoundError:
        pass
    iclient.create(index=INDEX, body={
        'mappings': {
            DOC_TYPE: {
                'properties': {
                    'location': {
                        'type': 'geo_point'
                    }
                }
            }
        }
    })


def push():
    host = os.environ.get('ELASTICSEARCH_HOST', 'localhost')
    connection = Elasticsearch([host])

    # delete old markers or do initial setup
    try:
        print(connection.delete_by_query(index=[INDEX], doc_type=DOC_TYPE, q='*'))
    except NotFoundError:
        set_mapping()

    # TODO use `bulk` to make this faster
    for row in get_data():
        connection.create(
            index=INDEX,
            doc_type=DOC_TYPE,
            body=row,
            id=row['atlas_number'],
        )

if __name__ == '__main__':
    push()
    # set_mapping()
