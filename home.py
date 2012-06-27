""" PubRefDb: Publication database web application.

Home page; list of most recent publications.
"""

from .base import *


class Home(MethodMixin, GET):
    "PubRefDb home page; list of most recent publications."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                AtomRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_operations(self, request):
        "For admin login: Edit PI list."
        ops = super(Home, self).get_data_operations(request)
        if self.is_login_admin():
            ops.append(dict(title='Edit PI list',
                            href=request.application.get_url('pilist')))
        return ops

    def get_data_resource(self, request):
        publications = self.get_docs('publication/published',
                                     '9999', last='0',
                                     descending=True,
                                     limit=configuration.MOST_RECENT_LIMIT)
        # Already sorted by the index
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title='Most recent publications',
                    resource='Home',
                    publications=publications)
