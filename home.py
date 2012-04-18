""" PubRefDb: Publication database web application.

Home page; list of most recent publications.
"""

from .method_mixin import *


class Home(MethodMixin, GET):
    "PubRefDb home page; list of most recent publications."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                PublicationsListHtmlRepresentation]

    def get_data_operations(self, request):
        ops = []
        if self.is_login_admin():
            ops.append(dict(title='PubMed import',
                            href=request.application.get_url('pubmed')))
            ops.append(dict(title='Edit PI list',
                            href=request.application.get_url('pilist')))
        return ops

    def get_data_resource(self, request):
        limit = 10
        publications = self.get_docs('publication/published',
                                     '9999', last='0',
                                     descending=True,
                                     limit=limit)
        # Already sorted by the index
        for publication in publications:
            self.normalize_publication(publication, request.application.get_url)
        return dict(title='SciLifeLab recent publications',
                    resource='Home',
                    publications=publications)
