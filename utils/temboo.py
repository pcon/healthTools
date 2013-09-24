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

"""This class is used to send data via Temboo"""

__author__ = "Patrick Connelly (patrick@deadlypenguin.com)"
__version__ = "1.0-0"

import os
import sys
import json
import base64
import urllib2
import httplib
import argparse
import gpx 
import ConfigParser

CFG_KEY_NAME = 'app_key_name'
CFG_KEY_VALUE = 'app_key_value'
CFG_ACCT = 'account_name'
CFG_PRESET = 'preset_name'

KEY_PRESET = 'preset'
KEY_INPUTS = 'inputs'
KEY_NAME = 'name'
KEY_VALUE = 'value'
KEY_ACTIVITY = 'Activity'
KEY_STATUS = 'status'
KEY_EXEC = 'execution'

TO_RUNKEEPER = 'runkeeper'
TO_TYPES = [TO_RUNKEEPER]

VIA_TEMBOO = 'temboo'
VIA_TYPES = [VIA_TEMBOO]

def create_config(fname):
    if os.path.isfile(fname):
        print "Config file '%s' already exists" % (fname,)
        sys.exit(-1)

    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(fname))
    except IOError:
        config.add_section(VIA_TEMBOO)
        config.set(VIA_TEMBOO, CFG_KEY_NAME, 'APP_KEY_NAME')
        config.set(VIA_TEMBOO, CFG_KEY_VALUE, 'APP_KEY_VALUE')
        config.set(VIA_TEMBOO, CFG_ACCT, 'ACCOUNT_NAME')
        config.set(VIA_TEMBOO, CFG_PRESET, 'PRESET_NAME')

        root_dir = os.path.dirname(fname)

        if not os.path.isdir(root_dir):
            os.mkdir(root_dir)

        with open(fname, 'wb') as configfile:
            config.write(configfile)

def send_to_rktemboo(data, config):
    base64string = base64.encodestring('%s:%s' % (config.get(VIA_TEMBOO, CFG_KEY_NAME), config.get(VIA_TEMBOO, CFG_KEY_VALUE))).replace('\n', '')

    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'
    headers['x-temboo-domain'] = "/%s/master" % (config.get(VIA_TEMBOO, CFG_ACCT),)
    headers['Authorization'] = "Basic %s" % (base64string,)

    url = "https://%s.temboolive.com/temboo-api/1.0/choreos/Library/RunKeeper/FitnessActivities/RecordActivity" % (config.get(VIA_TEMBOO, CFG_ACCT))

    try:
        request = urllib2.Request(url, json.dumps(data), headers)
        f = urllib2.urlopen(request)
        json.loads(f.read())
        f.close()
    except urllib2.HTTPError, e:
        print 'HTTPError: ' + str(e.code)
        sys.exit(-1)
    except urllib2.URLError, e:
        print 'HTTPError: ' + str(e.reason)
        sys.exit(-1)
    except httplib.HTTPException, e:
        print 'HTTPException: ' + str(e)
        sys.exit(-1)
    except Exception:
        import traceback
        print 'generic exception: ' + traceback.format_exc()
        sys.exit(-1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A tool to convert from GPX to RunKeeper via Temboo')

    parser.add_argument('-i', '--input', action='store', help='The input file', dest='input_file', metavar='INPUTFILE', required=True)
    parser.add_argument('-c', '--config', action='store', help='The config location', dest='config_file', metavar='CONFIGFILE')
    parser.add_argument('-t', '--to', action='store', help='What service to push to', dest='whereto', default=TO_RUNKEEPER, choices=TO_TYPES)
    parser.add_argument('--via', action='store', help='How to send data', dest='via', default=VIA_TEMBOO, choices=VIA_TYPES)

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print "Input file '%s' does not exist" % (args.input_file,)
        sys.exit(-1)

    if not args.config_file:
        args.config_file = '~/.healthtools/%s.conf' % (args.whereto)

    if not os.path.isfile(os.path.expanduser(args.config_file)):
        print "Config file '%s' does not exist" % (os.path.expanduser(args.config_file),)
        create_config(os.path.expanduser(args.config_file))
        print "  Default config file created"
        sys.exit(-1)

    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser(args.config_file)))

    ifp = open(args.input_file, 'r')
    gpx_data = ifp.read()
    ifp.close()

    data = {}

    if args.whereto == TO_RUNKEEPER:
        if args.via == VIA_TEMBOO:
            data[KEY_PRESET] = config.get(VIA_TEMBOO, CFG_PRESET) 
            data[KEY_INPUTS] = []
            activity = {}
            activity[KEY_NAME] = KEY_ACTIVITY
            activity[KEY_VALUE] = json.dumps(gpx.convert_gpx_to_rkjson(gpx_data))
            data[KEY_INPUTS].append(activity)
            send_to_rktemboo(data, config)