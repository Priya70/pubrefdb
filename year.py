""" PubRefDb: Publication database web application.

List of publications during one year.
"""

from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from .method_mixin import *
from .html_representation import *


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
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title="Publications: %s" % year,
                    resource='Publication list year',
                    publications=publications)
