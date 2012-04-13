""" PubRefDb: Publication database web application.

List of publications during one year.
"""

from .method_mixin import *


class Year(MethodMixin, GET):
    "List of publications during one year."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        year = request.variables['year']
        publications = self.query_docs('publication/published',
                                       year + '-13', last=year,
                                       descending=True)
        # Already sorted by index
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title="Publications: %s" % year,
                    resource='Publication list year',
                    publications=publications)
