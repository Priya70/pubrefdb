""" PubRefDb: Publication database web application.

List of publications with PubMed xref having incomplete data.
"""

from .base import *


class Incomplete(MethodMixin, GET):
    "List of publications with PubMed xref having incomplete data."

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        publications = self.get_docs('publication/incomplete', None)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title='Publications: Incomplete data',
                    resource='Publication incomplete',
                    publications=publications)
