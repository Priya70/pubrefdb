""" PubRefDb: Web application for a database of publications.

Base and mixin classes.
"""

import logging
import os
import uuid

import couchdb

from wrapid.methods import *
from wrapid.login import LoginMixin
from wrapid.utils import to_ascii
from wrapid.json_representation import JsonRepresentation

from . import configuration
from . import mimeutils
from .html_representation import *
from .medline_representation import *
from .atom_representation import *


def get_author_name(author):
    "Get the full name representation from the author dictionary."
    try:
        name = author['lastname']
        if not name: raise KeyError
        try:
            initials = author['initials']
            if not initials: raise KeyError
            name += ' ' + initials
        except KeyError:
            pass
    except KeyError:
        name = author.get('forename', 'unknown')
    return name


class MethodMixin(LoginMixin):
    "Mixin class for Method subclasses; database connect and authentication."

    def prepare(self, request):
        "Connect to the master database and authenticate the user login."
        self.set_login(request)
        self.db = configuration.get_db()
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
        try:
            self.publication = dict(self.db[request.variables['iui']])
        except couchdb.http.ResourceNotFound:
            raise HTTP_NOT_FOUND
        if self.publication['entitytype'] != 'publication':
            raise HTTP_NOT_FOUND

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
        "Return the links data."
        get_url = request.application.get_url
        links = []
        if configuration.PARENT_URL:
            link = dict(href=configuration.PARENT_URL,
                        title=configuration.PARENT_TITLE or 'Parent page')
            if configuration.PARENT_LOGO:
                link['image'] = configuration.PARENT_LOGO
            links.append(link)
        links.append(dict(title='Most recent',
                          href=get_url()))
        links.append(dict(title='Search',
                          href=get_url('search')))
        if self.is_login_admin():
            links.append(dict(title='Administration: Edit PI list',
                              href=get_url('pilist')))
            links.append(dict(title='Administration: Add publication',
                              href=get_url('publication')))
            links.append(dict(title='Administration:PubMed import',
                              href=get_url('pubmed', 'import')))
            links.append(dict(title='Administration:PubMed fetched',
                              href=get_url('pubmed', 'fetched')))
        years = self.get_years()
        for year in reversed(sorted(years.keys())):
            links.append(dict(title="Year (all PIs): %s" % year,
                              href=get_url('year', str(year)),
                              count=years[year]))
        try:
            doc = self.db['pilist']
        except couchdb.http.ResourceNotFound:
            pass
        else:
            pis = doc['pis']
            pis.sort(lambda i, j: cmp(i['name'].lower(), j['name'].lower()))
            for pi in pis:
                name = pi['name']
                key = to_ascii(name).lower().replace(' ', '_')
                links.append(dict(title="Principal Investigator: %s" % name,
                                  href=get_url('author', key)))
        ## for item in self.db.view('publication/tags', group=True):
        ##     links.append(dict(title="Tags: %s" % item.key,
        ##                       href=get_url('tag', item.key)))
        links.append(dict(title='Recently modified',
                          href=get_url('modified')))
        links.append(dict(title='Incomplete info',
                          href=get_url('incomplete')))
        links.append(dict(title='Journals',
                          href=get_url('journals')))
        return links

    def get_data_documentation(self, request):
        get_url = request.application.get_url
        return [dict(title='About',
                     href=get_url('doc')),
                dict(title='API',
                     href=get_url('doc/api'))]

    def get_years(self):
        """Get a dictionary where the keys are the publication years
        and the values are the total number of publications for the year.
        """
        view = self.db.view('publication/years', group=True)
        return dict([(int(r.key), r.value) for r in view])

    def get_docs(self, indexname, key, last=None, distinct=True, **kwargs):
        """Get the list of documents using the named index
        and the given key or interval.
        """
        kwargs['include_docs'] = True
        view = self.db.view(indexname, **kwargs)
        if key is None:
            iterator = view
        elif last is None:
            iterator = view[key]
        else:
            iterator = view[key:last]
        result = []
        lookup = set()
        for item in iterator:
            if distinct and item.id in lookup: continue
            result.append(item.doc)
            lookup.add(item.id)
        return result

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
            name = get_author_name(author)
            name = to_ascii(name.replace(' ', '_')).lower()
            author['href'] = get_url('author', name)
        return publication

    def sort_publications(self, publications, reverse=False):
        "Sort publications by published data, descending."
        if reverse:
            func = lambda i, j: cmp(j['published'], i['published'])
        else:
            func = lambda i, j: cmp(i['published'], j['published'])
        publications.sort(func)
        publications.reverse()

    def get_publication_files(self, iui, get_url):
        "Get the name, size and URL for all files attached to the publication."
        datadir = os.path.join(configuration.DATA_DIR, iui)
        result = []
        pos = len(datadir) + 1
        for dirpath, dirnames, filenames in os.walk(datadir):
            filenames.sort()
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                result.append(dict(filename=filepath[pos:],
                                   size=os.path.getsize(filepath),
                                   href=get_url('file', filepath[pos:])))
        return result
