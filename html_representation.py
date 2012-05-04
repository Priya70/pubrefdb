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

    def get_head(self):
        head = super(HtmlRepresentation, self).get_head()
        for outrepr in self.data.get('outreprs', []):
            if outrepr['mimetype'] == 'application/atom+xml':
                head.append(LINK(rel='alternate',
                                 type=outrepr['mimetype'],
                                 title='Atom feed',
                                 href=outrepr['href']))
                break
        return head

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
                result.append(str(A(self.safe(name), href=url)))
        return ', '.join(result)

    def format_journal(self, journal):
        if not journal: return '-'
        title = self.safe(journal['abbreviation'] or journal['title'])
        volume = self.safe(journal['volume'] or '-')
        issue = self.safe(journal['issue'] or '-')
        pages = self.safe(journal['pages'] or '-')
        return "%s, %s (%s) %s" % (title, B(volume), issue, pages)

    def format_tags(self, tags):
        if not tags: return '-'
        return self.safe(', '.join(tags))

    def get_xdb_link(self, publication, xdb, title=None, icon=None):
        xdb = xdb.lower()
        for xref in publication['xrefs']:
            if xref['xdb'].lower() == xdb:
                return self.get_xref_link(xref, title=title, icon=icon)
        return None

    def get_xref_link(self, xref, title=None, icon=None):
        xdb = xref['xdb']
        if title is None:
            title = "%(xdb)s:%(xkey)s" % xref
        elif not title:
            title = ''
        title = self.safe(title)
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
            info = []
            journal = publication.get('journal')
            if journal:
                info.append(self.format_journal(journal))
            published = publication.get('published')
            if published:
                info.append(published)
            link = self.get_xdb_link(publication, 'pubmed',
                                     title='PubMed',
                                     icon='pubmed')
            if link:
                info.append(link)
            link = self.get_xdb_link(publication, 'doi',
                                     title='Article',
                                     icon='xref')
            if link:
                info.append(link)
            table = TABLE(TR(TH(A(self.get_icon('page'),
                                  ' ',
                                  self.safe(publication['title']),
                                  href=publication['href']))),
                          TR(TD(self.format_authors(publication['authors']))),
                          TR(TD(', '.join([str(i) for i in info]))))
            rows.append(TR(TD(table)))
        if count:
            rows.insert(0, TD(I("%s publications" % len(rows))))
        return TABLE(klass='publications', *rows)


class PublicationsListHtmlRepresentation(PublicationsListMixin,
                                         HtmlRepresentation):
    "Display a list of publications."

    def get_content(self):
        return self.get_publications_list()


class FormHtmlRepresentation(FormHtmlMixin, HtmlRepresentation):
    "HTML representation of the form page for data input."
    pass
