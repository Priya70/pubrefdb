""" PubRefDb: Web application for a database of publications.

Load all documents from a dump into the database.
"""

import json

import couchdb

from pubrefdb import configuration


def undump(db, infile):
    data = json.load(infile)
    for id, doc in data.iteritems():
        try:
            del doc['_rev']
        except KeyError:
            pass
        try:
            olddoc = db[id]
        except couchdb.http.ResourceNotFound:
            pass
        else:
            doc['_rev'] = olddoc['_rev']
        db.save(doc)
        print id, doc['entitytype']


if __name__ == '__main__':
    infile = open('dump.json')
    undump(configuration.get_db(), infile)
    infile.close()
