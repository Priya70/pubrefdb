""" PubRefDb: Publication database web application.

List of publications with PubMed xref having incomplete information.
"""

from .base import *


class Incomplete(MethodMixin, GET):
    """Publications whose entries lack information about publication date,
    publication month, type of publication, journal, volume or pages."""

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListCountHtmlRepresentation]

    def get_data_resource(self, request):
        publications = self.get_docs('publication/incomplete', None)
        self.sort_publications(publications, reverse=True)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title='Incomplete information',
                    resource='Publication incomplete',
                    publications=publications,
                    descr=self.__doc__)
