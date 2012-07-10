""" PubRefDb: Publication database web application.

Search for publications.
"""

from .base import *

# Must be kept in sync with title.js
RSTRIP = '-\.:,?'
IGNORE = {
    'a': 1,
    'an': 1,
    'and': 1,
    'are': 1,
    'as': 1,
    'at': 1,
    'but': 1,
    'by': 1,
    'can': 1,
    'for': 1,
    'from': 1,
    'into': 1,
    'in': 1,
    'is': 1,
    'of': 1,
    'on': 1,
    'or': 1,
    'that': 1,
    'the': 1,
    'to': 1,
    'using': 1,
    'with': 1
    }

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
                MedlineRepresentation,
                AtomRepresentation,
                SearchHtmlRepresentation]

    fields = [StringField('terms', length=40, title='Terms')]

    def get_data_resource(self, request):
        values = self.parse_fields(request)
        try:
            terms = values['terms']
            if not terms: raise KeyError
            terms = terms.strip()
            if not terms: raise KeyError
            terms = terms.split(',')
            terms = [t.strip() for t in terms]
        except KeyError:
            result = []
            terms = []
        result = self.search_xrefs(terms)
        if not result:
            result = self.search_authors(terms)
            title_result = self.search_title(terms)
            if result:
                if title_result:        # Limit authors by title words
                    result.intersection_update(title_result)
            else:
                result = title_result
        if len(result) == 1:
            raise HTTP_SEE_OTHER(Location=request.application.get_url(result.pop()))
        publications = [self.db[i] for i in result]
        self.sort_publications(publications)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        override = dict(terms=dict(default=', '.join(terms)))
        return dict(title='Publications search',
                    resource='Publication list search',
                    publications=publications,
                    form=dict(fields=self.get_data_fields(override=override),
                              label='Search',
                              method='GET',
                              href=request.get_url()))

    def search_xrefs(self, terms):
        "Return union of all publications id's for xdb:xref terms."
        view = self.db.view('publication/xref')
        result = set()
        for term in terms:
            try:
                xdb, xkey = term.split(':', 1)
            except ValueError:
                xdb = 'pubmed'
                xkey = term
            items = view[[xdb.lower(), xkey]]
            result.update(set([i.id for i in items]))
        return result

    def search_authors(self, terms):
        "Return intersection of all publication id's for author names."
        view = self.db.view('publication/author')
        result = set()
        for term in terms:
            author = to_ascii(term)
            items = view[author : author+'Z']
            items = set([i.id for i in items])
            if len(items) > 0:
                if result:
                    result.intersection_update(items)
                else:
                    result = items
        return result

    def search_title(self, terms):
        "Return intersection of all publication id's for title words."
        view = self.db.view('publication/title')
        result = set()
        terms = [t.rstrip(RSTRIP) for t in terms]
        terms = [t for t in terms if t not in IGNORE]
        if not terms: return result
        for term in terms:
            items = view[term : term+'Z']
            items = set([i.id for i in items])
            if len(items) > 0:
                if result:
                    result.intersection_update(items)
                else:
                    result = items
        return result
