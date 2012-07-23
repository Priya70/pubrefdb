""" PubRefDb: Publication database web application.

List of publications recently modified.
"""

from .base import *


class Modified(MethodMixin, GET):
    "List of publications recently modified."

    DEFAULT_LIMIT = 20

    fields = [IntegerField('limit')]

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        values = self.parse_fields(request)
        try:
            limit = values['limit']
            if not limit or limit < 0: raise KeyError
        except KeyError:
            limit = self.DEFAULT_LIMIT
        publications = self.get_docs('publication/modified', 'X',
                                     last='0',
                                     descending=True,
                                     limit=limit)
        # Already sorted by the index
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title="Recently modified",
                    resource='Publication list modified',
                    publications=publications)
