""" PubRefDb: Publication database web application.

Home page; list of most recent publications.
"""

from .method_mixin import *


class Home(MethodMixin, GET):
    "PubRefDb home page; list of most recent publications."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_operations(self, request):
        ops = []
        if self.is_login_admin():
            ops.extend(self.get_data_main_operations(request))
        return ops

    def get_data_resource(self, request):
        LIMIT = 10
        publications = self.get_docs('publication/published',
                                     '9999', last='0',
                                     descending=True,
                                     limit=LIMIT)
        # Already sorted by the index
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title='Most recent publications',
                    resource='Home',
                    publications=publications)
