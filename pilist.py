""" PubRefDb: Publication database web application.

Edit list of PIs (authors for navigation menu links).
"""

from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .method_mixin import *
from .html_representation import *


class DisplayPiList(MethodMixin, GET):
    "Display PI list edit."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [MultiSelectField('remove', title='PIs',
                               check=False,
                               descr='Check the PIs to remove from the list.'),
              StringField('add', title='New PI',
                          descr="New PI to add to list."
                          " Specify using PubMed notation; 'Lastname IN',"
                          " where IN are the initials.")]

    def is_accessible(self):
        return self.is_login_admin()

    def get_data_resource(self, request):
        try:
            doc = self.db['pilist']
        except couchdb.http.ResourceNotFound:
            doc = dict()
        override = dict(remove=dict(options=doc.get('names', [])))
        return dict(title='PI list',
                    form=dict(fields=self.get_data_fields(override=override),
                              title='Edit PI list',
                              label='Save',
                              href=request.get_url(),
                              cancel=request.application.get_url()))


class ModifyPiList(MethodMixin, RedirectMixin, POST):
    "Modify the PI list."

    fields = DisplayPiList.fields

    def is_accessible(self):
        return self.is_login_admin()

    def process(self, request):
        try:
            doc = self.db['pilist']
        except couchdb.http.ResourceNotFound:
            doc = None
            names = []
        else:
            names = doc['names']
        values = self.parse_fields(request)
        try:
            remove = values['remove']
            if not remove: raise KeyError
        except KeyError:
            pass
        else:
            for name in remove:
                name = configuration.to_ascii(unicode(name))
                name = name.lower()
                for i, pi in enumerate(names):
                    if pi is None: continue
                    if pi.lower() == name:
                        names[i] = None
            names = [n for n in names if n is not None]
        try:
            name = values['add']
            if not name: raise KeyError
            name = name.strip()
            if not name: raise KeyError
        except KeyError:
            pass
        else:
            name = configuration.to_ascii(unicode(name))
            if name not in names:
                names.append(name)
        names.sort()
        if doc:
            doc['names'] = names
        else:
            doc = dict(_id='pilist',
                       entitytype='metadata',
                       names=names)
        self.db.save(doc)
        self.set_redirect(request.get_url())
