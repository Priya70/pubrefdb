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
        return "%s %s (%s) %s" % (journal['abbreviation'] or journal['title'],
                                  B(journal['volume'] or '-'),
                                  journal['issue'] or '-',
                                  journal['pages'] or '-')

    def get_xdb_link(self, publication, xdb):
        xdb = xdb.lower()
        for xref in publication['xrefs']:
            if xref['xdb'].lower() == xdb:
                return self.get_xref_link(xref)
        return None

    def get_xref_link(self, xref):
        xdb = xref['xdb']
        title = "%(xdb)s:%(xkey)s" % xref
        try:
            url = configuration.XDB_URL[xdb.lower()]
        except KeyError:
            return title
        return A(title, href=url % xref['xkey'])
        


class PublicationsListMixin(object):
    "Mixin to display list of publications."

    def get_publications_list(self):
        table = TABLE()
        for publication in self.data['publications']:
            parts = []
            journal = publication.get('journal')
            if journal:
                parts.append(self.format_journal(journal))
            published = publication.get('published')
            if published:
                parts.append(published)
            for xdb in ['pubmed', 'doi']:
                link = self.get_xdb_link(publication, xdb)
                if link:
                    parts.append(str(link))
            table.append(TR(TD(TABLE(
                TR(TD(A(self.get_icon('information'),
                        href=publication['href'])),
                   TH(self.safe(publication['title']))),
                TR(TD(rowspan=2),
                   TD(self.format_authors(publication['authors']))),
                TR(TD(', '.join(parts))),
                klass='publication'))))
        if not len(table):
            table.append(TR(TD(I('[none]'))))
        return table


class PublicationsListHtmlRepresentation(PublicationsListMixin,
                                         HtmlRepresentation):
    "Display a list of publications."

    def get_content(self):
        return self.get_publications_list()


class FormHtmlRepresentation(FormHtmlMixin, HtmlRepresentation):
    "HTML representation of the form page for data input."
    pass
