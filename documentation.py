""" PubRefDb: Publication database web application.

Produce the documentation for the web resource API by introspection.
"""

from wrapid.documentation import *
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .html_representation import *
from .method_mixin import MethodMixin


class ApiDocumentationHtmlRepresentation(ApiDocumentationHtmlMixin,
                                         HtmlRepresentation):
    "Apply Adhoc look to the documentation."

    stylesheets = ['static/standard.css']


class ApiDocumentation(MethodMixin, GET_ApiDocumentation):
    "Produce the documentation for the web resource API by introspection."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                ApiDocumentationHtmlRepresentation]
