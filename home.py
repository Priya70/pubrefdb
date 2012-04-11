""" PubRefDb: Publication database web application.

Home page; list of most recent publications.
"""

from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from .method_mixin import *
from .html_representation import *


class GET_Home(MethodMixin, GET):
    "PubRefDb home page; list of most recent publications."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_resource(self, request):
        limit = 10
        publications = self.query_docs('publication/published',
                                       '9999', last='0',
                                       descending=True,
                                       limit=limit)
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title="Publications: %i most recent" % limit,
                    resource='Home',
                    publications=publications)
