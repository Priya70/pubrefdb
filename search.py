""" PubRefDb: Publication database web application.

Search for publications.
"""

import urllib

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

    def get_descr(self):
        descr = super(SearchHtmlRepresentation, self).get_descr()
        descr += str(self.get_form())
        descr += str(P("%i publications." % len(self.data['publications'])))
        return descr
                   
    def get_content(self):
        return self.get_publications_list()

    def get_search(self):
        "The search form field is located at the top of the content panel."
        return ''


class Search(MethodMixin, GET):
    """The search terms may be cross-references to external databases,
    PubMed identifers, author names, title words or journal name abbreviation.
    """

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                SearchHtmlRepresentation]

    fields = [StringField('terms', length=40, title='Terms')]

    def prepare(self, request):
        super(Search, self).prepare(request)
        values = self.parse_fields(request)
        try:
            self.terms = values['terms']
            if not self.terms: raise KeyError
            self.terms = self.terms.strip()
            if not self.terms: raise KeyError
            self.terms = [t.strip() for t in self.terms.split(',')]
        except KeyError:
            self.terms = []

    def get_data_resource(self, request):
        result = self.search_xrefs()
        if not result:
            result = self.search_authors()
            title_result = self.search_title()
            if result:
                if title_result:        # Limit authors by title words
                    result.intersection_update(title_result)
            else:
                result = title_result
            journal_result = self.search_journal()
            if result:
                if journal_result:      # Limit authors by journal name
                    result.intersection_update(journal_result)
            else:
                result = journal_result
        if len(result) == 1:
            raise HTTP_SEE_OTHER(Location=request.application.get_url(result.pop()))
        publications = [self.db[i] for i in result]
        self.sort_publications(publications)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        override = dict(terms=dict(default=', '.join(self.terms)))
        return dict(title='Search',
                    resource='Publication list search',
                    publications=publications,
                    descr=self.__doc__,
                    form=dict(fields=self.get_data_fields(override=override),
                              label='Search',
                              method='GET',
                              href=request.get_url()))

    def get_data_outreprs(self, request):
        "Return the outrepr links response data, adding query to URLs."
        outreprs = super(Search, self).get_data_outreprs(request)
        if self.terms:
            terms = urllib.urlencode([('terms', ', '.join(self.terms))])
            for outrepr in outreprs:
                outrepr['href'] += '?' + terms
        return outreprs

    def search_xrefs(self):
        "Return union of all publications id's for xdb:xref terms."
        view = self.db.view('publication/xref')
        result = set()
        for term in self.terms:
            try:
                xdb, xkey = term.split(':', 1)
            except ValueError:
                xdb = 'pubmed'
                xkey = term
            items = view[[xdb.lower(), xkey]]
            result.update(set([i.id for i in items]))
        return result

    def search_authors(self):
        "Return intersection of all publication id's for author names."
        view = self.db.view('publication/author')
        result = set()
        for term in self.terms:
            author = to_ascii(term)
            items = view[author : author+'Z']
            items = set([i.id for i in items])
            if len(items) > 0:
                if result:
                    result.intersection_update(items)
                else:
                    result = items
        return result

    def search_title(self):
        "Return intersection of all publication id's for title words."
        view = self.db.view('publication/title')
        result = set()
        terms = [t.rstrip(RSTRIP) for t in self.terms]
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

    def search_journal(self):
        view = self.db.view('publication/journal')
        result = set()
        for term in self.terms:
            items = view[term]
            items = set([i.id for i in items])
            if len(items) > 0:
                if result:
                    result.intersection_update(items)
                else:
                    result = items
        return result
