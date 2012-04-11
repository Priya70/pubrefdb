""" PubRefDb: Publication database web application.

Search for publications.
"""

from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .method_mixin import *
from .html_representation import *


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
        try:
            terms = values['terms']
            if not terms: raise KeyError
            terms = terms.strip()
            if not terms: raise KeyError
        except KeyError:
            publications = []
            terms = ''
        else:
            author = configuration.to_ascii(unicode(terms))
            author = author.lower()
            publications = self.query_docs('publication/author',
                                           author, author + 'Z')
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        self.sort_publications(publications)
        override = dict(terms=dict(default=terms))
        return dict(title='Publications search',
                    resource='Publication list search',
                    publications=publications,
                    form=dict(fields=self.get_data_fields(override=override),
                              label='Search',
                              method='GET',
                              href=request.get_url()))
