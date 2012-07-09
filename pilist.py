""" PubRefDb: Publication database web application.

Edit list of PIs (authors for navigation menu links).
"""

from .base import *
from .database import MetadataSaver


class EditPiList(MethodMixin, GET):
    "Display edit page for PI list."

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                FormHtmlRepresentation]

    fields = [MultiSelectField('remove', title='PIs',
                               check=False,
                               descr='Check the PIs to remove from the list.'),
              StringField('add', title='Add PI',
                          descr="Add or update PI in the list."
                          " Use PubMed notation; 'Lastname IN',"
                          " where IN are the initials, and a blank"
                          " separates the name and initials."),
              StringField('affiliation', title='Affiliation',
                          length=60, maxlength=1000,
                          descr='Affiliation of the added/updated PI.'
                          ' A comma-separated list of affiliation strings'
                          ' to be used for the automated reference searches.'),
              HiddenField('rev',
                          required=True,
                          descr='Couchdb document revision')]

    def is_accessible(self):
        return self.is_login_admin()

    def get_data_resource(self, request):
        try:
            doc = self.db['pilist']
        except couchdb.http.ResourceNotFound:
            doc = dict()
        options = [dict(value=pi['name'],
                        title="%(name)s (%(affiliation)s)" % pi)
                   for pi in doc['pis']]
        override = dict(remove=dict(options=options))
        values = dict(rev=doc.get('_rev'))
        return dict(title='PI list',
                    form=dict(title='Edit PI list',
                              fields=self.get_data_fields(override=override),
                              values=values,
                              label='Save',
                              href=request.get_url(),
                              cancel=request.application.get_url()))


class ModifyPiList(MethodMixin, RedirectMixin, POST):
    "Modify the PI list."

    fields = EditPiList.fields

    def is_accessible(self):
        return self.is_login_admin()

    def process(self, request):
        try:
            doc = self.db['pilist']
        except couchdb.http.ResourceNotFound:
            doc = dict(pis=[])
        pis = dict()
        for pi in doc['pis']:
            pis[to_ascii(pi['name'])] = pi
        values = self.parse_fields(request)
        try:
            saver = MetadataSaver(self.db, doc=doc, values=values)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        try:
            remove = values['remove']
            if not remove: raise KeyError
        except KeyError:
            pass
        else:
            for name in remove:
                name = to_ascii(name)
                try:
                    del pis[name]
                except KeyError:
                    pass
        try:
            name = values['add']
            if not name: raise KeyError
            name = name.strip()
            if not name: raise KeyError
        except KeyError:
            pass
        else:
            normalized_name = to_ascii(name)
            pis[normalized_name] = dict(name=name,
                                        normalized_name=normalized_name,
                                        affiliation=values.get('affiliation') or '')
        with saver:
            doc['pis'] = [pis[key] for key in sorted(pis.keys())]
        self.set_redirect(request.get_url())
