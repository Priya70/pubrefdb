""" PubRefDb: Web application for a database of publications.

Mixin class for methods: authentication and database connection.
"""

import logging
import os
import uuid
import time

import couchdb

from wrapid.methods import *
from wrapid.login import LoginMixin
from wrapid.utils import now, to_ascii
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .html_representation import *


class DocumentSaver(object):
    "Context handler saving (update or create) a document in the database."

    # Must be specified by inheriting class
    entitytype = None

    def __init__(self, db, doc=dict(), values=dict()):
        assert self.entitytype
        self.db = db
        self.doc = doc
        if self.doc.has_key('_id'):     # Doc exists in the database
            try:
                rev = values.get('_rev', values['rev'])
                if rev != self.doc['_rev']:
                    raise ValueError('document revision mismatch;'
                                     ' someone else has edited the document')
            except KeyError:
                raise ValueError('document revision missing')
        else:
            self.doc['_id'] = uuid.uuid4().hex
            self.doc['entitytype'] = self.entitytype
            self.doc['created'] = now()

    def __enter__(self):
        return self.doc

    def __exit__(self, type, value, tb):
        if type is not None: return False # No exceptions handled here
        self.doc['modified'] = now()
        self.db.save(self.doc)

    def update(self, data):
        self.doc.update(data)


class PublicationSaver(DocumentSaver):
    "Context handler saving a publication document in the database."
    entitytype = 'publication'

class MetadataSaver(DocumentSaver):
    "Context handler saving a metadata document in the database."
    entitytype = 'metadata'


class MethodMixin(LoginMixin):
    "Mixin class for Method subclasses; database connect and authentication."

    def prepare(self, request):
        "Connect to the master database and authenticate the user login."
        self.set_login(request)
        server = couchdb.Server(configuration.COUCHDB_SERVER)
        self.db = server[configuration.COUCHDB_DATABASE]
        self.set_current(request)
        self.check_access(request.application.name)

    def get_account(self, name, password=None):
        """Return a dictionary describing the account:
        name, description, email, teams and properties.
        If password is provided, authenticate the account.
        Raise KeyError if there is no such account.
        Raise ValueError if the password does not match.
        """
        return configuration.users.get_account(name, password)

    def get_account_anonymous(self):
        "Return the dictionary describing the anonymous account."
        return configuration.users.get_account('anonymous')

    def set_current(self, request):
        "Set the current entities to operate on."
        pass

    def set_current_account(self, request):
        """Set the account to operate on; special case.
        This handles the case where an account name contains a dot
        and a short (<=4 chars) last name, which will otherwise
        be confused for a FORMAT specification.
        """
        try:
            self.account = self.get_account(request.variables['account'])
        except KeyError:
            if not request.variables.get('FORMAT'):
                raise HTTP_NOT_FOUND
            name = request.variables['account'] + request.variables['FORMAT']
            try:
                self.account = self.get_account(name)
            except KeyError:
                raise HTTP_NOT_FOUND
            request.undo_format_specifier('account')

    def set_current_publication(self, request):
        "Set the publication to operate on."
        self.publication = dict(self.db[request.variables['iui']])

    def check_access(self, realm):
        """Check that login account may access this resource.
        Raise HTTP FORBIDDEN if login user is not allowed to read this.
        Raise HTTP_UNAUTHORIZED if anonymous user.
        """
        if not self.is_accessible():
            if self.login['name'] == 'anonymous':
                raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
            else:
                raise HTTP_FORBIDDEN("disallowed for '%(name)s'" % self.login)

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return True

    def is_login_admin(self):
        """Is the login user 'admin', or is member of admin team,
        or is member of 'PubRefDb' team?
        """
        if self.login['name'] == 'admin': return True
        if 'admin' in self.login['teams']: return True
        if 'PubRefDb' in self.login['teams']: return True
        return False

    def get_data_links(self, request):
        "Return the links response data."
        get_url = request.application.get_url
        links = [dict(title='Search',
                      href=get_url('search'))]
        now = time.localtime()
        for year in xrange(2010, now.tm_year+1):
            links.append(dict(title="Year: %s" % year,
                              href=get_url('year', str(year))))
        try:
            doc = self.db['pilist']
        except couchdb.http.ResourceNotFound:
            pass
        else:
            for pi in doc['pis']:
                name = pi['name']
                url = get_url('author', name.replace(' ', '_'))
                links.append(dict(title="PIs: %s" % name, href=url))
        links.append(dict(title='Documentation: About',
                          href=get_url('about')))
        links.append(dict(title='Documentation: API',
                          href=get_url('doc')))
        return links

    def query_docs(self, indexname, key, last=None,
                   descending=False, limit=None):
        """Query the named index using the given key, or interval.
        Return a list of complete documents.
        """
        kwargs = dict(include_docs=True, descending=descending)
        if limit is not None:
            kwargs['limit'] = limit
        view = self.db.view(indexname, **kwargs)
        if key is None:
            iterator = view
        elif last is None:
            iterator = view[key]
        else:
            iterator = view[key:last]
        return [dict(i.doc) for i in iterator]

    def normalize_publication(self, publication, get_url):
        """Normalize the contents of the publication:
        Change key '_id' to 'iui' and '_rev' to 'rev'.
        Remove the '_attachments' entry.
        Add the 'href' entry.
        Add the 'alt_href' entry, if slug defined.
        Add 'href' to each author."""
        publication['iui'] = publication.pop('_id')
        publication['rev'] = publication.pop('_rev')
        publication['href'] = get_url(publication['iui'])
        slug = publication.get('slug')
        if slug:
            publication['alt_href'] = get_url(slug)
        publication.pop('_attachments', None)
        for author in publication['authors']:
            try:
                name = "%(lastname)s_%(initials)s" % author
            except KeyError:
                name = author['forename']
            name = name.replace(' ', '_')
            name = to_ascii(name)
            author['href'] = get_url('author', name)
        return publication

    def sort_publications(self, publications):
        "Sort publications by published data, descending."
        publications.sort(lambda i, j: cmp(i['published'], j['published']))
        publications.reverse()

    def get_publication_files(self, iui, get_url):
        datadir = os.path.join(configuration.DATA_DIR, iui)
        result = []
        pos = len(datadir) + 1
        for dirpath, dirnames, filenames in os.walk(datadir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                result.append(dict(filename=filepath[pos:],
                                   size=os.path.getsize(filepath),
                                   href=get_url('file', filepath[pos:])))
        return result
