""" PubRefDb: Web application for a database of publications.

Dump all documents having a defined entitytype to a file.
"""

import json

from pubrefdb import configuration


def dump(db, outfile):
    data = dict()
    for id in db:
        doc = db[id]
        if doc.has_key('entitytype'):
            data[doc['_id']] = dict(doc)
            print id, doc['entitytype']
    json.dump(data, outfile)


if __name__ == '__main__':
    outfile = open('dump.json', 'wb')
    dump(configuration.get_db(), outfile)
    outfile.close()