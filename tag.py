""" PubRefDb: Publication database web application.

List of publications having a given tag.
"""

from .base import *


class Tag(MethodMixin, GET):
    "List of publications having a given tag."

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        tag = request.variables['tag']
        publications = self.get_docs('publication/tag', tag)
        self.sort_publications(publications)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title="Publications: %s" % tag,
                    resource='Publication list tag',
                    publications=publications)
