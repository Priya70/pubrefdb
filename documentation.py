""" PubRefDb: Publication database web application.

Produce the documentation for the web resource API by introspection.
"""

from wrapid.documentation import *

from .base import *


class ApiDocumentationHtmlRepresentation(ApiDocumentationHtmlMixin,
                                         HtmlRepresentation):
    stylesheets = ['static/standard.css']


class ApiDocumentation(MethodMixin, GET_ApiDocumentation):
    "Produce the documentation for the web resource API by introspection."

    outreprs = [JsonRepresentation,
                ApiDocumentationHtmlRepresentation]
