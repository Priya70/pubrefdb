""" PubRefDb: Web application for a database of publications.

Configuration settings.
"""

import logging
import os.path
import sys
import socket
import urllib
import time
import datetime

import couchdb


DEBUG = False

HOST = None                       # Dict(href, title, admin, email)

PARENT_URL = None                 # URL to parent page, if any
PARENT_TITLE = None               # Parent page title, if any
PARENT_LOGO = None                # URL for image for parent page, if any.

COUCHDB_SERVER   = 'http://localhost:5984/'
COUCHDB_DATABASE = 'pubrefdb'

DATA_DIR = '/var/local/pubrefdb'

DATE_FORMAT     = '%Y-%m-%d'
DAY_FORMAT      = '%A %d %B %Y'
DATETIME_FORMAT = '%Y-%m-%d %H:%M'

XDB_URL = dict(pubmed='http://www.ncbi.nlm.nih.gov/pubmed/%s',
               doi='http://dx.doi.org/%s')

MIMETYPE_ICONS = {'application/pdf': 'pdf',
                  'application/msword': 'word',
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'word',
                  'application/vnd.ms-powerpoint': 'ppt',
                  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'ppt',
                  'application/vnd.ms-excel': 'excel',
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xls',
                  'text/plain': 'txt',
                  'text/csv': 'csv',
                  'image/png': 'image',
                  'image/gif': 'image',
                  'image/jpeg': 'image',
                  'application/octet-stream': 'bin'}

# Fallback user account interface; should be overriden by proper implementation
import fallback_users as users


#----------------------------------------------------------------------
# Do not change anything below this.
#----------------------------------------------------------------------
# The 'site_XXX' module may redefine any of the above global variables.
HOSTNAME = socket.gethostname()
MODULENAME = "pubrefdb.site_%s" % HOSTNAME
try:
    __import__(MODULENAME)
except ImportError:
    raise NotImplementedError("host %s" % HOSTNAME)
else:
    module = sys.modules[MODULENAME]
    for key in dir(module):
        if key.startswith('_'): continue
        globals()[key] = getattr(module, key)
#----------------------------------------------------------------------


if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

SOURCE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(SOURCE_DIR, 'static')

README_FILE = os.path.join(SOURCE_DIR, 'README.md')


def get_db():
    "Get an opened database interface instance."
    server = couchdb.Server(COUCHDB_SERVER)
    try:
        return server[COUCHDB_DATABASE]
    except couchdb.http.ResourceNotFound:
        raise KeyError('database does not exist')

def get_date(value=None, format=DATE_FORMAT):
    "Get the date in ISO format. Use current local time if value is None."
    if value is None:
        value = time.localtime()
    elif isinstance(value, (datetime.date, datetime.datetime)):
        value = value.timetuple()
    elif isinstance(value, time.struct_time):
        pass
    elif isinstance(value, basestring):
        value = time.strptime(value, format)
    elif isinstance(value, int):
        value = datetime.datetime.now() + datetime.timedelta(value)
        value = value.timetuple()
    else:
        raise ValueError('cannot convert given date value')
    return time.strftime(format, value)

def get_day(value=None, format=DAY_FORMAT):
    "Get the date in informal format. Use current local time if value is None."
    return get_date(value=value, format=format)
