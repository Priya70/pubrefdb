""" PubRefDb: Publication database web application.

List of publications with PubMed xref having incomplete information.
"""

from .base import *


class Incomplete(MethodMixin, GET):
    """The publications whose entries lack information about publication date,
    publication month, type of publication, journal, volume or pages."""

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        publications = self.get_docs('publication/incomplete', None)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title='Incomplete information',
                    resource='Publication incomplete',
                    publications=publications,
                    description=self.__doc__)
