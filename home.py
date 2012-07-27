""" PubRefDb: Publication database web application.

Home page; list of most recent publications.
"""

from .base import *


class Home(MethodMixin, GET):
    "The 10 most recent publications."

    MOST_RECENT_LIMIT = 10

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        publications = self.get_docs('publication/published',
                                     '9999', last='0',
                                     descending=True,
                                     limit=self.MOST_RECENT_LIMIT)
        # Already sorted by the index
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title='PubRefDb: Publications database',
                    resource='Home',
                    publications=publications,
                    descr=self.__doc__)
