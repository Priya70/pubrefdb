""" PubRefDb: Publication database web application.

Edit list of PIs (authors for navigation menu links).
"""

from .method_mixin import *


class EditPiList(MethodMixin, GET):
    "Display edit page for PI list."

    outreprs = [JsonRepresentation,
                TextRepresentation,
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
                          length=60,
                          descr='Affiliation of the added/updated PI.'
                          ' A comma-separated list of affiliation strings'
                          ' to be used for the automated reference searches.')]

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
        return dict(title='PI list',
                    form=dict(fields=self.get_data_fields(override=override),
                              title='Edit PI list',
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
            doc = dict(_id='pilist',
                       entitytype='metadata',
                       pis=[])
        pis = dict([(pi['name'], pi['affiliation']) for pi in doc['pis']])
        values = self.parse_fields(request)
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
            name = to_ascii(name)
            affiliation = values.get('affiliation') or ''
            pis[name] = affiliation.strip()
        keys = sorted(pis.keys())
        doc['pis'] = [dict(name=key, affiliation=pis[key]) for key in keys]
        self.db.save(doc)
        self.set_redirect(request.get_url())
