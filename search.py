""" PubRefDb: Publication database web application.

Search for publications.
"""

from .method_mixin import *


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
                publications.extend(self.search_pmid(term))
                publications.extend(self.search_author(term))
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

    def search_pmid(self, pmid):
        return self.query_docs('publication/pmid', pmid)

    def search_author(self, author):
        author = to_ascii(author).lower()
        return self.query_docs('publication/author', author, author + 'Z')
