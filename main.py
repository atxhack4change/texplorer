import csv
import os
import re

from elasticsearch import Elasticsearch


INDEX = 'thc'
DOC_TYPE = 'marker'


def find_years(text):
    try:
        matches = re.findall(r"\d{4}", text)
        # print "{}, {}".format(text[0:40], len(matches))
        return matches
    except TypeError:
        return []


# def write(dataset, path='data/output.csv'):
#     with open(path, 'w') as csvfile:
#         writer = csv.writer(csvfile)
#         for row in dataset.validators=[]lues:
#             cad = str(find_years(row[15]))
#             writer.writerow(row.tolist() + [cad])


def get_data(path='data/Historical Marker_20150521_145030_254.csv'):
    with open(path, 'r') as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            text = row['markertext']
            row['address'] = row['address'].strip()
            # add our own data
            row['years'] = find_years(text)
            yield row


def push():
    host = os.environ.get('ELASTICSEARCH_HOST', 'localhost')
    connection = Elasticsearch([host])
    for row in get_data():
        connection.create(
            index=INDEX,
            doc_type=DOC_TYPE,
            body=row,
            id=row['atlas_number'],
        )

push()
