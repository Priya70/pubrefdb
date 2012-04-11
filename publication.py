""" PubRefDb: Publication database web application.

Publication resources.
"""

import uuid

from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation
from wrapid.utils import now

from . import configuration
from .method_mixin import *
from .html_representation import *
from pubrefdb import pubmed


class PublicationHtmlRepresentation(HtmlRepresentation):
    "Display all details for a publication."

    def get_content(self):
        table = TABLE(TR(TH('Authors'),
                         TD(self.format_authors(self.data['authors']))),
                      TR(TH('Published'),
                         TD(self.data['published'])),
                      klass='details')
        journal = self.data.get('journal')
        if journal:
            table.append(TR(TH('Journal'),
                            TD(self.format_journal(journal))))
        abstract = self.data.get('abstract')
        if abstract:
            table.append(TR(TH('Abstract'),
                            TD(abstract)))
        return table

    def get_metadata(self):
        table = TABLE()
        for xref in self.data['xrefs']:
            table.append(TR(TD(self.get_xref_link(xref))))
        return table


class Publication(MethodMixin, GET):
    "Display information about a given publication."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                PublicationHtmlRepresentation]

    def get_data_resource(self, request):
        publication = dict(self.db[request.variables['iui']])
        self.normalize_publication(publication, request.application.get_url)
        return publication


class InputPublicationPubmed(MethodMixin, GET):
    "Display input page for importing publication from PubMed."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = (StringField('pmid', title='PubMed identifier',
                          required=True,
                          descr='Give the PubMed numerical identifier'
                          ' for the publication to add.'),)

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def get_data_resource(self, request):
        return dict(title='Import publication',
                    form=dict(title='Import publication from PubMed',
                              fields=self.get_data_fields(),
                              label='Add',
                              href=request.url,
                              cancel=request.application.url))


class ImportPublicationPubmed(MethodMixin, RedirectMixin, POST):
    "Import publication from PubMed."

    fields = InputPublicationPubmed.fields

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def process(self, request):
        values = self.parse_fields(request)
        pmid = values['pmid']
        article = pubmed.Article(pmid)
        if not article.pmid:
            raise HTTP_BAD_REQUEST("no article with PMID %s" % pmid)
        doc = self.db.view('publication/pmid')[article.pmid]
        if not doc:
            doc = article.get_data()
            doc['_id'] = uuid.uuid4().hex
            doc['entitytype'] = 'publication'
            doc['created'] = now()
            doc['modified'] = now()
            self.db.save(doc)
        self.set_redirect(request.application.get_url(doc['_id']))
