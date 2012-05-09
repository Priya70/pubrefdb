""" PubRefDb: Publication database web application.

About page, describing the system software.
"""

from .base import *


class About(MethodMixin, GET):
    "About page, describing the system software."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                HtmlRepresentation]

    def get_data_resource(self, request):
        return dict(resource='About',
                    descr=open(configuration.README_FILE).read())
