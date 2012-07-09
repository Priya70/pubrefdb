""" PubRefDb: Publication database web application.

List of publications for one author.
"""

from .base import *
from .medline_representation import MedlineRepresentation


class Author(MethodMixin, GET):
    "List of publications for one author."

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

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
        name = ' '.join([s.capitalize() for s in author.split('_')])
        return dict(title="Publications: %s" % name,
                    resource='Publication list author',
                    publications=publications)
