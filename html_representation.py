""" PubRefDb: Publication database web application.

General HTML representation class.
"""

import logging

from wrapid.html_representation import *

from . import configuration


class HtmlRepresentation(BaseHtmlRepresentation):
    "Base class for HTML representation of the resource."

    logo        = 'static/scilifelab_logo_small.png'
    favicon     = 'static/favicon.ico'
    stylesheets = ['static/standard.css']

    def get_icon(self, name):
        return IMG(src=self.get_url('static', "%s.png" % name),
                   alt=name, title=name, width=16, height=16)

    def get_mimetype_icon(self, mimetype):
        try:
            filename = configuration.MIMETYPE_ICONS[mimetype]
        except KeyError:
            return ''
        else:
            return self.get_icon(filename)

    def format_authors(self, authors):
        if not authors: return '-'
        result = []
        for author in authors:
            try:
                name = "%(lastname)s %(initials)s" % author
            except KeyError:
                name = author['forename']
            try:
                url = author['href']
            except KeyError:
                result.append(name)
            else:
                result.append(str(A(name, href=url)))
        return ', '.join(result)

    def format_journal(self, journal):
        if not journal: return '-'
        return "%s %s (%s) %s" % (journal['abbreviation'] or journal['title'],
                                  B(journal['volume'] or '-'),
                                  journal['issue'] or '-',
                                  journal['pages'] or '-')

    def format_tags(self, tags):
        if not tags: return '-'
        return ', '.join(tags)

    def get_xdb_link(self, publication, xdb, title=None, icon=None):
        xdb = xdb.lower()
        for xref in publication['xrefs']:
            if xref['xdb'].lower() == xdb:
                return self.get_xref_link(xref, title=title, icon=icon)
        return None

    def get_xref_link(self, xref, title=None, icon=None):
        xdb = xref['xdb']
        if not title:
            title = "%(xdb)s:%(xkey)s" % xref
        try:
            url = configuration.XDB_URL[xdb.lower()]
        except KeyError:
            return title
        url = url  % xref['xkey']
        if icon:
            return A(self.get_icon(icon), title, href=url, klass='xref')
        else:
            return A(title, href=url, klass='xref')


class PublicationsListMixin(object):
    "Mixin to display list of publications."

    def get_publications_list(self, count=True):
        rows = []
        for publication in self.data['publications']:
            details = []
            journal = publication.get('journal')
            if journal:
                details.append(self.format_journal(journal))
            published = publication.get('published')
            if published:
                details.append(published)
            links = []
            link = self.get_xdb_link(publication, 'pubmed',
                                     title='PubMed', icon='pubmed')
            if link:
                links.append(str(link))
            link = self.get_xdb_link(publication, 'doi',
                                     title='Article', icon='xref')
            if link:
                links.append(str(link))
            rows.append(TR(TD(TABLE(
                TR(TD(A(self.get_icon('information'),
                        href=publication['href'])),
                   TD(B(self.safe(publication['title'])),
                      ' ',
                      ' '.join(links))),
                TR(TD(rowspan=2),
                   TD(self.format_authors(publication['authors']))),
                TR(TD(', '.join(details))),
                klass='publication'))))
        if count:
            rows.insert(0, TD(I("%s publications" % len(rows))))
        return TABLE(*rows)


class PublicationsListHtmlRepresentation(PublicationsListMixin,
                                         HtmlRepresentation):
    "Display a list of publications."

    def get_content(self):
        return self.get_publications_list()


class FormHtmlRepresentation(FormHtmlMixin, HtmlRepresentation):
    "HTML representation of the form page for data input."
    pass
