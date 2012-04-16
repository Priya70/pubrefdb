""" PubRefDb: Publication database web application.

Publication resources.
"""

import logging
import shutil
import uuid

from wrapid.file import File

from .method_mixin import *
from pubrefdb import pubmed
from pubrefdb import mimeutils


class PublicationHtmlRepresentation(HtmlRepresentation):
    "Display all details for a publication."

    def get_content(self):
        table = TABLE(TR(TH('Authors'),
                         TD(self.format_authors(self.data['authors']))),
                      klass='details')
        journal = self.data.get('journal')
        if journal:
            table.append(TR(TH('Journal'),
                            TD(self.format_journal(journal))))
        table.append(TR(TH('Published'),
                        TD(self.data['published'])))
        affiliation = self.data.get('affiliation')
        if affiliation:
            table.append(TR(TH('Affiliation'),
                            TD(affiliation)))
        abstract = self.data.get('abstract')
        if abstract:
            table.append(TR(TH('Abstract'),
                            TD(abstract)))
        url = self.data.get('alt_href')
        if url:
            table.append(TR(TH('Slug URL'),
                            TD(A(url, href=url))))
        files = self.data.get('files')
        filetable = TABLE()
        for file in files:
            filename = file['filename']
            mimetype, encoding = mimeutils.guess_type(filename)
            icon = self.get_mimetype_icon(mimetype)
            filetable.append(TR(TD(icon),
                                TD("%(size)s bytes" % file, klass='integer'),
                                TD(A(file['filename'], href=file['href']))))
        if len(filetable) == 0:
            filetable.append(TR(TD(I('[none]'))))
        table.append(TR(TH('Files'),
                        TD(filetable)))
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

    def set_current(self, request):
        self.set_current_publication(request)
        self.normalize_publication(self.publication,
                                   request.application.get_url)

    def get_data_operations(self, request):
        ops = super(Publication, self).get_data_operations(request)
        if self.is_login_admin():
            ops.append(dict(title='Edit slug',
                            href=request.get_url('slug')))
            ops.append(dict(title='Edit files',
                            href=request.get_url('file')))
            ops.append(dict(title='Delete',
                            href=request.url,
                            method='DELETE'))
        return ops

    def get_data_resource(self, request):
        self.publication['files'] = self.get_publication_files(self.publication['iui'],
                                                               request.get_url)
        return self.publication


class DeletePublication(MethodMixin, RedirectMixin, DELETE):
    "Delete the publication."

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def set_current(self, request):
        self.set_current_publication(request)

    def process(self, request):
        iui = self.publication['_id']
        shutil.rmtree(os.path.join(configuration.DATA_DIR, iui),
                      ignore_errors=True)
        del self.db[iui]
        self.set_redirect(request.application.url)


class EditPublicationSlug(MethodMixin, GET):
    "Display edit form for the slug of a publication."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [StringField('slug', title='Slug',
                          descr='Alternative path for the publication URL;'
                          ' more memorable and user-friendly.'),
              HiddenField('rev',
                          required=True,
                          descr='Couchdb document revision')]

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def set_current(self, request):
        self.set_current_publication(request)

    def get_data_resource(self, request):
        values = dict(slug=self.publication.get('slug'),
                      rev=self.publication.get('_rev'))
        cancel = request.application.get_url(self.publication['_id'])
        return dict(title="Edit slug for '%s'" % self.publication['title'],
                    form=dict(title='Edit publication slug',
                              fields=self.get_data_fields(),
                              values=values,
                              label='Save',
                              href=request.url,
                              cancel=cancel))


class ModifyPublicationSlug(MethodMixin, RedirectMixin, POST):
    "Modify the slug of the publication."

    fields = EditPublicationSlug.fields

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def set_current(self, request):
        self.set_current_publication(request)

    def process(self, request):
        values = self.parse_fields(request)
        try:
            saver = PublicationSaver(self.db, self.publication, values)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        slug = values.get('slug')
        if slug:
            slug = slug.strip()
            slug = slug.lower()
            slug = slug.replace(' ', '-')
        if slug != self.publication.get('slug'):
            if slug:
                # Check if slug already defined for other publication
                if self.query_docs('publication/slug', slug):
                    raise HTTP_CONFLICT("slug '%s' already in use")
            else:
                slug = None
            with saver:
                self.publication['slug'] = slug
        self.set_redirect(request.application.get_url(self.publication['_id']))


class PublicationFile(MethodMixin, File):
    "Get the file attached to the publication."

    as_attachment = True

    def prepare(self, request):
        MethodMixin.prepare(self, request)
        File.prepare(self, request)

    def set_current(self, request):
        self.set_current_publication(request)

    def get_dirpath(self, request):
        return os.path.join(configuration.DATA_DIR, self.publication['_id'])


class EditPublicationFile(MethodMixin, GET):
    "Display edit page for attaching or deleting a file for the publication. "

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [MultiSelectField('delete', title='Delete',
                               boxes=True, check=False,
                               descr='Delete the checked attached files.'),
              FileField('attach', title='Attach',
                        descr='Attach the given file.')]

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def set_current(self, request):
        self.set_current_publication(request)

    def get_data_resource(self, request):
        files = self.get_publication_files(self.publication['_id'],
                                           request.get_url)
        override = dict(delete=dict(options=[f['filename'] for f in files]))
        return dict(title='Edit attached files',
                    form=dict(title='Edit attached files',
                              fields=self.get_data_fields(override=override),
                              label='Update',
                              href=request.url,
                              cancel=request.url))


class ModifyPublicationFile(MethodMixin, RedirectMixin, POST):
    "Modify the list of files attached to the publication."

    fields = EditPublicationFile.fields

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def set_current(self, request):
        self.set_current_publication(request)

    def process(self, request):
        iui = self.publication['_id']
        datadir = os.path.join(configuration.DATA_DIR, iui)
        values = self.parse_fields(request)
        filenames = values.get('delete') or []
        for filename in filenames:
            filename = filename.lstrip('./~') # Remove dangerous characters
            os.remove(os.path.join(datadir, filename))
        attach = values.get('attach')
        if attach:
            if not os.path.exists(datadir):
                os.mkdir(datadir)
            filename = attach['filename']
            filename = filename.lstrip('./~') # Remove dangerous characters
            outfile = open(os.path.join(datadir, filename), 'w')
            outfile.write(attach['value'])
            outfile.close()
        self.set_redirect(request.application.get_url(iui))


class InputPubmedPublication(MethodMixin, GET):
    "Display input page for importing publication from PubMed."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [StringField('pmid', title='PubMed identifier',
                          required=True,
                          descr='Give the PubMed numerical identifier'
                          ' for the publication to add.')]

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


class ImportPubmedPublication(MethodMixin, RedirectMixin, POST):
    "Import publication from PubMed."

    fields = InputPubmedPublication.fields

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def process(self, request):
        values = self.parse_fields(request)
        pmid = values['pmid']
        result = list(self.db.view('publication/pmid')[pmid])
        if result:
            iui = result[0].id
        else:
            article = pubmed.Article(pmid)
            if not article.pmid:
                raise HTTP_BAD_REQUEST("no article with PMID %s" % pmid)
            with PublicationSaver(self.db) as ps:
                ps.update(article.get_data())
                iui = ps.doc['_id']
        self.set_redirect(request.application.get_url(iui))


class PubmedPublication(MethodMixin, RedirectMixin, GET):
    "Look up the publication for the given PMID, and redirect."

    def set_current(self, request):
        view = self.db.view('publication/pmid')
        result = list(view[request.variables['pmid']])
        if len(result) != 1:
            raise HTTP_NOT_FOUND
        self.set_redirect(request.application.get_url(result[0].id))


class SlugPublication(MethodMixin, RedirectMixin, GET):
    "Look up the publication for the given slug, and redirect."

    def set_current(self, request):
        view = self.db.view('publication/slug')
        result = list(view[request.variables['slug']])
        if len(result) != 1:
            raise HTTP_NOT_FOUND
        self.set_redirect(request.application.get_url(result[0].id))
