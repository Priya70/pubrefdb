""" PubRefDb: Publication database web application.

List of publications for one author.
"""

from .base import *
from .medline_representation import MedlineRepresentation


class Author(MethodMixin, GET):
    "Publications involving the specified author."

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListCountHtmlRepresentation]

    def get_data_resource(self, request):
        author = request.variables['author']
        author_normalized = to_ascii(author)
        author_normalized = author_normalized.lower()
        author_normalized = author_normalized.replace('_', ' ')
        publications = self.get_docs('publication/author',
                                     author_normalized,
                                     author_normalized + 'Z')
        self.sort_publications(publications)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        parts = author.split('_')
        name = parts[0].capitalize()
        for part in parts[1:]:
            if len(part) > 2:
                part = part.capitalize()
            else:
                part = part.upper()
            name += ' ' + part
        years = self.get_years().keys()
        descr = self.__doc__
        descr += """ NOTE: The list only includes publications
        for the years %s-%s.""" % (min(years), max(years))
        return dict(title="Author: %s" % name,
                    resource='Publication list author',
                    publications=publications,
                    descr=descr)
