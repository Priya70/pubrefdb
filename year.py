""" PubRefDb: Publication database web application.

List of publications during one year.
"""

from .base import *


class Year(MethodMixin, GET):
    "All publications for the given year, including all authors."

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        year = request.variables['year']
        publications = self.get_docs('publication/published',
                                     year + '-13', last=year,
                                     descending=True)
        # Already sorted by the index
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title="Year (all PIs): %s" % year,
                    resource='Publication list year',
                    publications=publications,
                    descr=self.__doc__)
