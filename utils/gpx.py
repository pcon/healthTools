#!/usr/bin/env python

# Copyright 2013 Patrick Connelly <patrick@deadlypenguin.com> 
#
# This file is part of healthTools
#
# healthTools is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

"""This class is used to convert GPX files to various formats"""

__author__ = "Patrick Connelly (patrick@deadlypenguin.com)"
__version__ = "1.1-0"

import os
import sys
import json
import argparse
from lxml import etree
from dateutil import tz
from dateutil.parser import parse

KEY_TYPE = 'type'
KEY_EQUIPMENT = 'equipment'
KEY_NOTES = 'notes'
KEY_PATH = 'path'
KEY_STARTTIME = 'start_time'
KEY_LAT = 'latitude'
KEY_LON = 'longitude'
KEY_TIMESTAMP = 'timestamp'
KEY_ALT = 'altitude'
KEY_FB = 'post_to_facebook'
KEY_TWIT = 'post_to_twitter'
KEY_FEATURES = 'features'
KEY_NAME = 'name'
KEY_PROP = 'properties'
KEY_TIME = 'time'
KEY_GEO = 'geometry'
KEY_COORDS = 'coordinates'

NAMESPACE = {'ns': 'http://www.topografix.com/GPX/1/1'}

TYPE_RK = 'runkeeper'
TYPE_GEOJSON = 'geojson'

OUTPUT_TYPES = [TYPE_RK, TYPE_GEOJSON]

DEFAULT_DATA = {
    TYPE_RK: {
        KEY_TYPE: 'Running',
        KEY_EQUIPMENT: 'None',
        KEY_NOTES: '',
        KEY_FB: False,
        KEY_TWIT: False
    }
}

def enrich_data(jdata, additional_data, data_type):
    for key in additional_data:
        if not key in jdata:
            jdata[key] = additional_data[key]
    for key in DEFAULT_DATA[data_type]:
        if not key in jdata:
            jdata[key] = DEFAULT_DATA[data_type][key]

def convert_gpx_to_rkjson(data, additional_data={}):
    jdata = {}
    jdata[KEY_PATH] = []

    tree = etree.fromstring(data)

    metadata_time = tree.xpath("//ns:metadata//ns:time", namespaces=NAMESPACE)

    start_time = None

    if len(metadata_time) > 0:
        start_time = parse(metadata_time[0].text)
    else:
        first_time = tree.xpath("//ns:time", namespaces=NAMESPACE)
        if len(first_time) > 0:
            start_time = parse(first_time[0].text)

    jdata[KEY_STARTTIME] = start_time.astimezone(tz.tzlocal()).strftime('%a, %d %b %Y %H:%M:%S')

    for point in tree.xpath("//ns:trk//ns:trkseg//ns:trkpt", namespaces=NAMESPACE):
        path_point = {}

        path_point[KEY_LAT] = float(point.get('lat'))
        path_point[KEY_LON] = float(point.get('lon'))
        path_point[KEY_TYPE] = 'gps'

        for element in point.iter('{' + NAMESPACE['ns'] + '}ele'):
            path_point[KEY_ALT] = float(element.text)

        for element in point.iter('{' + NAMESPACE['ns'] + '}time'):
            ts = parse(element.text)
            path_point[KEY_TIMESTAMP] = int((ts - start_time ).total_seconds())

        jdata[KEY_PATH].append(path_point)

        enrich_data(jdata, additional_data, TYPE_RK)

    return jdata

def convert_gpx_to_geojson(data, additional_data={}):
    jdata = {}
    jdata[KEY_TYPE] = "FeatureCollection"
    jdata[KEY_FEATURES] = []

    feature = {}
    feature[KEY_TYPE] = 'Feature'
    feature[KEY_PROP] = {}
    tree = etree.fromstring(data)

    feature[KEY_PROP][KEY_NAME] = tree.xpath("//ns:trk//ns:name", namespaces=NAMESPACE)[0].text
    start_time = parse(tree.xpath("//ns:metadata//ns:time", namespaces=NAMESPACE)[0].text)
    feature[KEY_PROP][KEY_TIME] = start_time.astimezone(tz.tzlocal()).strftime('%a, %d %b %Y %H:%M:%S')

    feature[KEY_GEO] = {}
    feature[KEY_GEO][KEY_TYPE] = 'LineString'
    feature[KEY_GEO][KEY_COORDS] = []

    for point in tree.xpath("//ns:trk//ns:trkseg//ns:trkpt", namespaces=NAMESPACE):
        path_point = []
        path_point.append(float(point.get('lon')))
        path_point.append(float(point.get('lat')))
        feature[KEY_GEO][KEY_COORDS].append(path_point)

    jdata[KEY_FEATURES].append(feature)

    return jdata

def convert_file(ifile, ofile, force=False, additional_data={}, format_type=TYPE_RK):
    if not os.path.isfile(ifile):
        print "Input file '%s' does not exist" % (ifile,)
        sys.exit(-1)

    if os.path.isfile(ofile) and not force:
        print "Output file '%s' exists. Use -f to overwrite" % (ofile,)
        sys.exit(-1)

    ifp = open(ifile, 'r')
    ofp = open(ofile, 'w')
    odata = ''

    if format_type == TYPE_RK:
        jdata = convert_gpx_to_rkjson(ifp.read(), additional_data=additional_data)
        odata = json.dumps(jdata)
    elif format_type == TYPE_GEOJSON:
        jdata = convert_gpx_to_geojson(ifp.read(), additional_data=additional_data)
        odata = json.dumps(jdata)

    ofp.write(odata)

    ifp.close()
    ofp.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A tool to convert from GPX to various formats')

    parser.add_argument('-i', action='store', help='The input file', dest='input_file', metavar='INPUTFILE', required=True)
    parser.add_argument('-o', action='store', help='The output file', dest='output_file', metavar='OUTPUTFILE', required=True)
    parser.add_argument('-f', action='store_true', help='Force overwriting output file', dest='force')
    parser.add_argument('--outputtype', action='store', help='The output type', dest='output_type', required=False, default=TYPE_RK, choices=OUTPUT_TYPES)

    args = parser.parse_args()
    convert_file(args.input_file, args.output_file, force=args.force, format_type=args.output_type)