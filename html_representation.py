""" PubRefDb: Publication database web application.

General HTML representation class.
"""

from wrapid.html_representation import *

from . import configuration


class HtmlRepresentation(BaseHtmlRepresentation):
    "Base class for HTML representation of the resource."

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
            filename = 'document'
        return self.get_icon(filename)

    def format_authors(self, doc):
        from .base import get_author_name
        authors = doc.get('authors')
        if not authors: return '-'
        result = []
        for author in authors:
            name = get_author_name(author)
            try:
                url = author['href']
            except KeyError:
                result.append(name)
            else:
                result.append(str(A(self.safe(name), href=url)))
        return ', '.join(result)

    def format_journal(self, doc):
        """Format journal volume, issue and pages.
        Handle special case of conference proceedings.
        """
        journal = doc.get('journal')
        if not journal: return '-'
        parts = [self.safe(journal['abbreviation'] or journal['title']),
                 str(B(self.safe(journal['volume'] or '-')))]
        type = doc.get('type')
        if type != 'conference proceedings':
            parts.append("(%s)" % self.safe(journal['issue'] or '-'))
            parts.append(self.safe(journal['pages'] or '-'))
        return ' '.join(parts)

    def format_tags(self, doc):
        tags = doc.get('tags')
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

    def get_publications_list(self):
        rows = []
        for publication in self.data['publications']:
            info = [self.format_journal(publication)]
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
                          TR(TD(self.format_authors(publication))),
                          TR(TD(', '.join([str(i) for i in info]))))
            rows.append(TR(TD(table)))
        return TABLE(klass='publications', *rows)


class PublicationsListHtmlRepresentation(PublicationsListMixin,
                                         HtmlRepresentation):
    "Display a list of publications."

    def get_content(self):
        return self.get_publications_list()


class PublicationsListCountHtmlRepresentation(PublicationsListHtmlRepresentation):
    "Display a list of publications, with count."

    def get_descr(self):
        descr = super(PublicationsListCountHtmlRepresentation, self).get_descr()
        descr += str(P("%i publications." % len(self.data['publications'])))
        return descr


class FormHtmlRepresentation(FormHtmlMixin, HtmlRepresentation):
    "HTML representation of the form page for data input."
    pass
