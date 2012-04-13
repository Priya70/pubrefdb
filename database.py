""" PubRefDb: Publication database web application.

Utility functions to create the database and load the design documents.
"""

import os

import couchdb

from pubrefdb import configuration


def get_db():
    "Get the existing database. Raise KeyError if it does not exist."
    server = couchdb.Server(configuration.COUCHDB_SERVER)
    try:
        return server[configuration.COUCHDB_DATABASE]
    except couchdb.http.ResourceNotFound:
        raise KeyError('database does not exist')

def create_db():
    "Create a new database."
    server = couchdb.Server(configuration.COUCHDB_SERVER)
    return server.create(configuration.COUCHDB_DATABASE)


def save(db, doc):
    "Update or create the document."
    try:
        doc['_rev'] = db.revisions(doc['_id']).next().rev
    except StopIteration:
        pass
    db.save(doc)


def load_pilist(db):
    "Load the first version of the PI list."

    try:
        doc = db['pilist']
    except couchdb.http.ResourceNotFound:
        doc = dict(_id='pilist',
                   entitytype='metadata',
                   pis=[dict(name='Lundeberg J',
                             affiliation='Royal Institute of Technology,'
                             ' Science for Life Laboratory'),
                        dict(name='Uhlen M',
                             affiliation='Royal Institute of Technology,'
                             ' Science for Life Laboratory'),
                        dict(name='Kere J',
                             affiliation='Karolinska Institute,'
                             ' Karolinska Institutet,'
                             ' Science for Life Laboratory')])
        save(db, doc)


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
        save(db, doc)


if __name__ == '__main__':
    try:
        db = get_db()
    except KeyError:
        print 'Creating the database...'
        db = create_db()
    print 'Loading PI list...'
    load_pilist(db)
    print 'Loading design documents...'
    load_designs(db)
