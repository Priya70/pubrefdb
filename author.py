""" PubRefDb: Publication database web application.

List of publications for one author.
"""

from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .method_mixin import *
from .html_representation import *


class Author(MethodMixin, GET):
    "List of publications for one author."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        author = request.variables['author']
        author_normalized = configuration.to_ascii(unicode(author))
        author_normalized = author_normalized.replace('_', ' ').lower()
        publications = self.query_docs('publication/author',
                                       author_normalized,
                                       author_normalized + 'Z')
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        self.sort_publications(publications)
        return dict(title="Publications: %s" % author.replace('_', ' '),
                    resource='Publication list author',
                    publications=publications)
