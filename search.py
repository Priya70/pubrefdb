""" PubRefDb: Publication database web application.

Search for publications.
"""

from .base import *


class SearchHtmlRepresentation(FormHtmlMixin,
                               PublicationsListMixin,
                               HtmlRepresentation):

    def get_search(self):
        return ''

    def get_content(self):
        return DIV(self.get_form(),
                   self.get_publications_list())


class Search(MethodMixin, GET):
    "Search for publications."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                AtomRepresentation,
                SearchHtmlRepresentation]

    fields = [StringField('terms', title='Terms')]

    def get_data_resource(self, request):
        values = self.parse_fields(request)
        publications = []
        try:
            terms = values['terms']
            if not terms: raise KeyError
            terms = terms.strip()
            if not terms: raise KeyError
        except KeyError:
            terms = ''
        else:
            for term in terms.split(','):
                term = term.strip()
                try:
                    xdb, xkey = term.split(':', 1)
                except ValueError:
                    xdb = 'pubmed'
                    xkey = term
                publications.extend(self.search_xref(xdb, xkey))
                publications.extend(self.search_author(term))
                publications.extend(self.search_journal(term))
        if len(publications) == 1:
            id = publications[0]['_id']
            raise HTTP_SEE_OTHER(Location=request.application.get_url(id))
        self.sort_publications(publications)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        override = dict(terms=dict(default=terms))
        return dict(title='Publications search',
                    resource='Publication list search',
                    publications=publications,
                    form=dict(fields=self.get_data_fields(override=override),
                              label='Search',
                              method='GET',
                              href=request.get_url()))

    def search_xref(self, xdb, xkey):
        return self.get_docs('publication/xref', [xdb.lower(), xkey])

    def search_author(self, author):
        author = to_ascii(author)
        return self.get_docs('publication/author', author, author + 'Z')

    def search_journal(self, journal):
        return self.get_docs('publication/journal', journal, journal + 'Z')
