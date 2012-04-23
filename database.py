""" PubRefDb: Publication database web application.

Utility functions to create the database and load the design documents.
"""

import os
import csv
import uuid

import couchdb

from wrapid.utils import now, to_ascii

from pubrefdb import configuration


class DocumentSaver(object):
    "Context handler saving (update or create) a document in the database."

    entitytype = None

    def __init__(self, db, doc=dict(), values=dict(), force=False):
        self.db = db
        self.doc = doc
        if self.doc.has_key('_id'):
            if values:
                try:
                    rev = values.get('_rev', values['rev'])
                    if rev != self.doc['_rev']:
                        raise ValueError('document revision mismatch;'
                                         ' document has been edited'
                                         ' by someone else')
                except KeyError:
                    raise ValueError('document revision missing')
            elif force:
                try:
                    doc['_rev'] = db.revisions(doc['_id']).next().rev
                except StopIteration:
                    pass
        else:
            self.doc['_id'] = uuid.uuid4().hex
            if self.entitytype and not self.doc.has_key('entitytype'):
                self.doc['entitytype'] = self.entitytype
                self.doc['created'] = now()

    def __enter__(self):
        return self.doc

    def __exit__(self, type, value, tb):
        if type is not None: return False # No exceptions handled here
        if self.entitytype:
            self.doc['modified'] = now()
        self.db.save(self.doc)


class PublicationSaver(DocumentSaver):
    "Context handler saving a publication document in the database."
    entitytype = 'publication'

class MetadataSaver(DocumentSaver):
    "Context handler saving a metadata document in the database."
    entitytype = 'metadata'


def load_pilist(db):
    "Load the first version of the PI list."
    if db.get('pilist'): return
    # Get the list from a CSV file
    doc = dict(_id='pilist',
               pis=[])
    pis = doc['pis']
    try:
        infile = open('data/pilist.csv')
    except IOError:
        pass
    else:
        reader = csv.reader(infile)
        for record in reader:
            name = record[0].strip()
            if not name: continue
            affiliations = [a.strip() for a in record[1:] if a.strip()]
            pis.append(dict(name=name,
                            normalized_name=to_ascii(name),
                            affiliation=', '.join(affiliations)))
    with MetadataSaver(db, doc):
        pass

def load_designs(db, root='designs'):
    for design in os.listdir(root):
        views = dict()
        path = os.path.join(root, design)
        if not os.path.isdir(path): continue
        path = os.path.join(root, design, 'views')
        for filename in os.listdir(path):
            name, ext = os.path.splitext(filename)
            if ext != '.js': continue
            with open(os.path.join(path, filename)) as codefile:
                code = codefile.read()
            if name.startswith('map_'):
                name = name[len('map_'):]
                key = 'map'
            elif name.startswith('reduce_'):
                name = name[len('reduce_'):]
                key = 'reduce'
            else:
                key = 'map'
            views.setdefault(name, dict())[key] = code
        doc = dict(_id="_design/%s" % design, views=views)
        with DocumentSaver(db, doc, force=True):
            pass


if __name__ == '__main__':
    try:
        db = configuration.get_db()
    except KeyError:
        print 'Creating the database...'
        server = couchdb.Server(configuration.COUCHDB_SERVER)
        db = server.create(configuration.COUCHDB_DATABASE)
    print 'Loading PI list (if any and not done)...'
    load_pilist(db)
    print 'Reloading design documents...'
    load_designs(db)
