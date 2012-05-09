""" PubRefDb: Publication database web application.

List of publications for one author.
"""

from .base import *


class Author(MethodMixin, GET):
    "List of publications for one author."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        author = request.variables['author']
        author_normalized = to_ascii(author)
        author_normalized = author_normalized.replace('_', ' ').lower()
        publications = self.get_docs('publication/author',
                                     author_normalized,
                                     author_normalized + 'Z')
        self.sort_publications(publications)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title="Publications: %s" % author.replace('_', ' '),
                    resource='Publication list author',
                    publications=publications)
