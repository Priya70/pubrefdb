""" PubRefDb: Publication database web application.

Publication resources.
"""

import logging
import shutil
import uuid

from wrapid.file import File

from .base import *
from . import pubmed
from .database import PublicationSaver


class PublicationHtmlRepresentation(HtmlRepresentation):
    "Display all details for a publication."

    def get_content(self):
        table = TABLE(TR(TH('Authors'),
                         TD(self.format_authors(self.data['authors']))),
                      TR(TH('Type'),
                         TD(self.safe(self.data.get('type')))),
                      TR(TH('Journal'),
                         TD(self.format_journal(self.data.get('journal')))),
                      TR(TH('Published'),
                         TD(self.safe(self.data.get('published') or '-'))),
                      TR(TH('Affiliation'),
                         TD(self.safe(self.data.get('affiliation') or '-'))),
                      TR(TH('Abstract'),
                         TD(self.safe(self.data.get('abstract') or '-'))),
                      TR(TH('Comment'),
                         TD(self.safe(self.data.get('comment') or '-'))),
                      TR(TH('Tags'),
                         TD(self.format_tags(self.data.get('tags')))),
                      klass='publication')
        url = self.data.get('alt_href')
        if url:
            table.append(TR(TH('Slug URL'),
                            TD(A(url, href=url))))
        hreftable = TABLE()
        for href in self.data['hrefs']:
            url = href['href']
            hreftable.append(TR(TD(A(href.get('title') or url, href=url))))
        if len(hreftable) == 0:
            hreftable.append(TR(TD('-')))
        files = self.data.get('files')
        table.append(TR(TH('Links'),
                        TD(hreftable)))
        filetable = TABLE()
        for file in files:
            filename = file['filename']
            mimetype, encoding = mimeutils.guess_type(filename)
            icon = self.get_mimetype_icon(mimetype)
            filetable.append(TR(TD(icon),
                                TD("%(size)s bytes" % file, klass='integer'),
                                TD(A(file['filename'], href=file['href']))))
        if len(filetable) == 0:
            filetable.append(TR(TD('-')))
        table.append(TR(TH('Files'),
                        TD(filetable)))
        return table

    def get_metadata(self):
        table = TABLE(TR(TH('External databases')))
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
        "For admin login: edit operations."
        ops = []
        if self.is_login_admin():
            ops.append(dict(title='Edit',
                            href=request.get_url('edit')))
            ops.append(dict(title='Edit tags',
                            href=request.get_url('tags')))
            ops.append(dict(title='Edit slug',
                            href=request.get_url('slug')))
            ops.append(dict(title='Edit links',
                            href=request.get_url('hrefs')))
            ops.append(dict(title='Edit files',
                            href=request.get_url('file')))
            ops.append(dict(title='Edit xrefs',
                            href=request.get_url('xrefs')))
            for xref in self.publication['xrefs']:
                if xref['xdb'].lower() == 'pubmed':
                    ops.append(dict(title='Update from PubMed',
                                    href=request.get_url('pubmed'),
                                    method='POST'))
                    break
            ops.append(dict(title='Delete',
                            href=request.url,
                            method='DELETE'))
            ops.append(dict(title='Exclude',
                            href=request.get_url('exclude')))
        return ops

    def get_data_resource(self, request):
        self.publication['files'] = \
            self.get_publication_files(self.publication['iui'],
                                       request.get_url)
        return self.publication


class InputPublication(MethodMixin, GET):
    "Display input form for adding a publication."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [StringField('title', title='Title',
                          required=True, length=80, maxlength=1000),
              TextField('authors', title='Authors',
                        required=True, rows=2, cols=60,
                        descr="Comma-separated author names, using "
                        " format 'Lastname IN', where IN are the initials."),
              StringField('type', title='Type',
                          required=True,
                          descr='Publication type.'),
              StringField('journal_title', title='Journal title',
                          length=40,
                          descr='Full title of journal.'),
              StringField('journal_abbrev', title='Abbrev title',
                          length=20,
                          descr='Abbreviated title of journal.'),
              StringField('journal_volume', title='Volume',
                          length=8,
                          descr='Journal volume.'),
              StringField('journal_issue', title='Issue',
                          length=8,
                          descr='Journal issue.'),
              StringField('journal_pages', title='Pages',
                          length=20,
                          descr='Publication pages in journal issue.'),
              StringField('published', title='Published',
                          required=True, length=10, maxlength=10,
                          descr="Date of publication. ISO format 'YYYY-MM-DD'"
                          " using '00' to denote unknown month or day."),
              StringField('affiliation', title='Affiliation',
                          length=80, maxlength=1000,
                          descr='Affiliation of authors.'),
              TextField('abstract', title='Abstract'),
              TextField('comment', title='Comment')]
    
    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def get_data_resource(self, request):
        values = dict(type='journal article')
        return dict(title='Add publication',
                    form=dict(title='Add publication',
                              fields=self.get_data_fields(),
                              values=values,
                              label='Add',
                              href=request.url,
                              cancel=request.application.url))

class AddPublication(MethodMixin, RedirectMixin, POST):
    "Add the publication."

    fields = InputPublication.fields

    def process(self, request):
        values = self.parse_fields(request)
        try:
            saver = PublicationSaver(self.db)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        with saver as doc:
            doc['title'] = values['title']
            authors = []
            for author in [a.strip() for a in values.get('authors').split(',')]:
                parts = author.split()
                if len(parts) >=2:
                    author = dict(lastname=' '.join(parts[:-1]),
                                  initials=parts[-1])
                    author['lastname_normalized'] = to_ascii(author['lastname'])
                    author['initials_normalized'] = to_ascii(author['initials'])
                else:
                    author = dict(lastname=parts[0])
                    author['lastname_normalized'] = to_ascii(author['lastname'])
                authors.append(author)
            doc['authors'] = authors
            doc['type'] = values.get('type')
            doc['journal'] = journal = dict()
            journal['title'] = values.get('journal_title')
            journal['abbreviation'] = values.get('journal_abbrev')
            journal['volume'] = values.get('journal_volume')
            journal['issue'] = values.get('journal_issue')
            journal['pages'] = values.get('journal_pages')
            doc['published'] = values.get('published')
            doc['affiliation'] = values.get('affiliation')
            doc['abstract']= values.get('abstract')
            doc['comment']= values.get('comment')
            doc['xrefs'] = []
            doc['hrefs'] = []
        self.set_redirect(request.application.get_url(doc['_id']))


class EditMixin(object):

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def set_current(self, request):
        self.set_current_publication(request)


class DeletePublication(EditMixin, MethodMixin, RedirectMixin, DELETE):
    "Delete the publication, no questions asked."

    def process(self, request):
        iui = self.publication['_id']
        shutil.rmtree(os.path.join(configuration.DATA_DIR, iui),
                      ignore_errors=True)
        del self.db[iui]
        self.set_redirect(request.application.url)


class VerifyExcludePublication(EditMixin, MethodMixin, GET):
    "Verify that the publication is to be excluded."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [CheckboxField('verify', title='Verify',
                            required=True,
                            descr='Really delete and exclude'
                            ' this publication permanently?')]

    def get_data_resource(self, request):
        return dict(title="Exclude '%s'" % self.publication['title'],
                    form=dict(title='Verify exclusion',
                              fields=self.get_data_fields(),
                              label='Exclude',
                              href=request.url,
                              cancel=request.get_url('..')))


class ExcludePublication(EditMixin, MethodMixin, RedirectMixin, POST):
    "Exclude the publication: add all xrefs to exclusion list, and delete."

    fields = VerifyExcludePublication.fields

    def process(self, request):
        values = self.parse_fields(request)
        if values.get('verify'):
            shutil.rmtree(os.path.join(configuration.DATA_DIR,
                                       self.publication['_id']),
                          ignore_errors=True)
            with PublicationSaver(self.db, doc=self.publication) as doc:
                doc['entitytype'] = 'excluded'
            self.set_redirect(request.application.url)
        else:
            self.set_redirect(request.get_url('..'))


class EditPublication(EditMixin, MethodMixin, GET):
    "Display edit form for basic fields of a publication."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = InputPublication.fields + \
             [HiddenField('rev',
                          required=True,
                          descr='Couchdb document revision')]

    def get_data_resource(self, request):
        journal = self.publication.get('journal') or dict()
        values = dict(title=self.publication['title'],
                      authors=', '.join([get_author_name(a)
                                         for a in self.publication['authors']]),
                      type=self.publication.get('type'),
                      journal_title=journal.get('title'),
                      journal_abbrev=journal.get('abbreviation'),
                      journal_volume=journal.get('volume'),
                      journal_issue=journal.get('issue'),
                      journal_pages=journal.get('pages'),
                      published=self.publication.get('published'),
                      affiliation=self.publication.get('affiliation'),
                      abstract=self.publication.get('abstract'),
                      comment=self.publication.get('comment'),
                      rev=self.publication.get('_rev'))
        return dict(title="Edit '%s'" % self.publication['title'],
                    form=dict(title='Edit publication',
                              fields=self.get_data_fields(),
                              values=values,
                              label='Save',
                              href=request.url,
                              cancel=request.get_url('..')))


class ModifyPublication(EditMixin, MethodMixin, RedirectMixin, POST):
    "Modify basic fields of the publication."

    fields = EditPublication.fields

    def process(self, request):
        values = self.parse_fields(request)
        try:
            saver = PublicationSaver(self.db, self.publication, values)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        with saver:
            self.publication['title'] = values.get('title')
            authors = []
            for author in [a.strip() for a in values.get('authors').split(',')]:
                parts = author.split()
                if len(parts) >=2:
                    author = dict(lastname=' '.join(parts[:-1]),
                                  initials=parts[-1])
                    author['lastname_normalized'] = to_ascii(author['lastname'])
                    author['initials_normalized'] = to_ascii(author['initials'])
                else:
                    author = dict(lastname=parts[0])
                    author['lastname_normalized'] = to_ascii(author['lastname'])
                authors.append(author)
            self.publication['authors'] = authors
            self.publication['type'] = values.get('type')
            try:
                journal = self.publication['journal']
            except KeyError:
                self.publication['journal'] = journal = dict()
            journal['title'] = values.get('journal_title')
            journal['abbreviation'] = values.get('journal_abbrev')
            journal['volume'] = values.get('journal_volume')
            journal['issue'] = values.get('journal_issue')
            journal['pages'] = values.get('journal_pages')
            self.publication['published'] = values.get('published')
            self.publication['affiliation'] = values.get('affiliation')
            self.publication['abstract']= values.get('abstract')
            self.publication['comment']= values.get('comment')
        self.set_redirect(request.get_url('..'))


class EditPublicationXrefs(EditMixin, MethodMixin, GET):
    "Display edit form for the xrefs of a publication."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [MultiSelectField('remove', title='Xrefs',
                               check=False, boxes=True,
                               descr='Check xrefs to remove from the list.'),
              StringField('add', title='Add xref',
                          descr="Add a new xref. Format 'xdb:xkey'."),
              HiddenField('rev',
                          required=True,
                          descr='Couchdb document revision')]

    def get_data_resource(self, request):
        options = []
        for xref in self.publication['xrefs']:
            options.append("%(xdb)s:%(xkey)s" % xref)
        override = dict(remove=dict(options=options))
        values = dict(rev=self.publication.get('_rev'))
        return dict(title="Edit xrefs for '%s'" % self.publication['title'],
                    form=dict(title='Edit publication xrefs',
                              fields=self.get_data_fields(override=override),
                              values=values,
                              label='Save',
                              href=request.url,
                              cancel=request.get_url('..')))


class ModifyPublicationXrefs(EditMixin, MethodMixin, RedirectMixin, POST):
    "Modify the xrefs of the publication."

    fields = EditPublicationXrefs.fields

    def process(self, request):
        values = self.parse_fields(request)
        try:
            saver = PublicationSaver(self.db, self.publication, values)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        with saver:
            xrefs = self.publication['xrefs']
            for remove in values.get('remove') or []:
                for i, xref in enumerate(xrefs):
                    if not xref: continue
                    xref = "%(xdb)s:%(xkey)s" % xref
                    if xref == remove:
                        xrefs[i] = None
            self.publication['xrefs'] = [x for x in xrefs if x]
            xref = values.get('add')
            if xref:
                try:
                    xdb, xkey = xref.split(':', 1)
                except ValueError:
                    raise HTTP_BAD_REQUEST('invalid new xref value')
                for xref in self.publication['xrefs']:
                    if xref['xdb'] == xdb and xref['xkey'] == xkey:
                        break
                else:
                    self.publication['xrefs'].append(dict(xdb=xdb, xkey=xkey))
        self.set_redirect(request.get_url('..'))


class EditPublicationHrefs(EditMixin, MethodMixin, GET):
    "Display edit form for the hrefs of a publication."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [MultiSelectField('remove', title='Hrefs',
                               check=False, boxes=True,
                               descr='Check hrefs to remove from the list.'),
              StringField('add', title='Add href',
                          descr='The URL if a new href.'),
              StringField('title', title='Title',
                          descr='The optional title for a new href.'),
              HiddenField('rev',
                          required=True,
                          descr='Couchdb document revision')]

    def get_data_resource(self, request):
        options = []
        for href in self.publication['hrefs']:
            try:
                title = href['title']
                if not title: raise KeyError
                title = "%s (%s)" % (title, href['href'])
            except KeyError:
                title = href['href']
            options.append(dict(value=href['href'], title=title))
        override = dict(remove=dict(options=options))
        values = dict(rev=self.publication.get('_rev'))
        return dict(title="Edit links for '%s'" % self.publication['title'],
                    form=dict(title='Edit publication hrefs',
                              fields=self.get_data_fields(override=override),
                              values=values,
                              label='Save',
                              href=request.url,
                              cancel=request.get_url('..')))


class ModifyPublicationHrefs(EditMixin, MethodMixin, RedirectMixin, POST):
    "Modify the hrefs of the publication."

    fields = EditPublicationHrefs.fields

    def process(self, request):
        values = self.parse_fields(request)
        try:
            saver = PublicationSaver(self.db, self.publication, values)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        with saver:
            hrefs = self.publication['hrefs']
            for remove in values.get('remove') or []:
                for i, href in enumerate(hrefs):
                    if not href: continue
                    if href['href'] == remove:
                        hrefs[i] = None
            self.publication['hrefs'] = [h for h in hrefs if h]
            url = values.get('add')
            title = values.get('title')
            for href in self.publication['hrefs']:
                if href['href'] == url:
                    href['title'] = title
                    break
            else:
                if url:
                    if title:
                        href = dict(href=url, title=title)
                    else:
                        href = dict(href=url)
                    self.publication['hrefs'].append(href)
        self.set_redirect(request.get_url('..'))


class EditPublicationTags(EditMixin, MethodMixin, GET):
    "Display edit form for the tags of a publication."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [MultiSelectField('tags', title='Tags',
                               check=False,
                               descr='Select tags to apply.'),
              StringField('add', title='Add',
                          descr='Add a new tag.'),
              HiddenField('rev',
                          required=True,
                          descr='Couchdb document revision')]

    def get_data_resource(self, request):
        view = self.db.view('publication/tags', group=True)
        override = dict(tags=dict(options=[v.key for v in view]))
        values = dict(rev=self.publication.get('_rev'),
                      tags=self.publication.get('tags') or [])
        return dict(title="Edit tags for '%s'" % self.publication['title'],
                    form=dict(title='Edit publication tags',
                              fields=self.get_data_fields(override=override),
                              values=values,
                              label='Save',
                              href=request.url,
                              cancel=request.get_url('..')))


class ModifyPublicationTags(EditMixin, MethodMixin, RedirectMixin, POST):
    "Modify the tags of the publication."

    fields = EditPublicationTags.fields

    def process(self, request):
        values = self.parse_fields(request)
        try:
            saver = PublicationSaver(self.db, self.publication, values)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        with saver:
            tags = values.get('tags') or []
            tag = values.get('add')
            if tag:
                if tag not in tags:
                    tags.append(tag)
            self.publication['tags'] = tags
        self.set_redirect(request.get_url('..'))


class EditPublicationSlug(EditMixin, MethodMixin, GET):
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

    def get_data_resource(self, request):
        values = dict(slug=self.publication.get('slug'),
                      rev=self.publication.get('_rev'))
        return dict(title="Edit slug for '%s'" % self.publication['title'],
                    form=dict(title='Edit publication slug',
                              fields=self.get_data_fields(),
                              values=values,
                              label='Save',
                              href=request.url,
                              cancel=request.get_url('..')))


class ModifyPublicationSlug(EditMixin, MethodMixin, RedirectMixin, POST):
    "Modify the slug of the publication."

    fields = EditPublicationSlug.fields

    def process(self, request):
        values = self.parse_fields(request)
        try:
            saver = PublicationSaver(self.db, self.publication, values)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        with saver:
            slug = values.get('slug')
            if slug:
                slug = slug.strip()
                slug = slug.lower()
                slug = slug.replace(' ', '-')
            # Check if slug already defined for other publication
            if slug and \
               slug != self.publication.get('slug') and \
               self.get_docs('publication/slug', slug):
                raise HTTP_CONFLICT("slug '%s' already in use" % slug)
            self.publication['slug'] = slug or None
        self.set_redirect(request.get_url('..'))


class UpdatePubmedPublication(EditMixin, RedirectMixin, MethodMixin, POST):
    """Update the entry from information in PubMed.
    Currently only the journal information (name, volume, issue, pages)
    is updated."""

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return self.is_login_admin()

    def process(self, request):
        for xref in self.publication['xrefs']:
            if xref['xdb'].lower() == 'pubmed':
                break
        else:
            raise HTTP_BAD_REQUEST('publication has no PubMed xref')
        article = pubmed.Article(xref['xkey'])
        if not article.pmid:
            raise HTTP_BAD_REQUEST("no article with PMID %s" % pmid)
        with PublicationSaver(self.db, doc=self.publication) as doc:
            doc['journal'] = article.journal
        self.set_redirect(request.application.get_url(doc['_id']))


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


class EditPublicationFile(EditMixin, MethodMixin, GET):
    "Display edit page for attaching or deleting a file for the publication. "

    outreprs = [JsonRepresentation,
                TextRepresentation,
                FormHtmlRepresentation]

    fields = [MultiSelectField('remove', title='Remove',
                               boxes=True, check=False,
                               descr='Check attached files to remove.'),
              FileField('attach', title='Attach',
                        descr='Attach the given file.')]

    def get_data_resource(self, request):
        files = self.get_publication_files(self.publication['_id'],
                                           request.get_url)
        override = dict(remove=dict(options=[f['filename'] for f in files]))
        return dict(title='Edit attached files',
                    form=dict(title='Edit attached files',
                              fields=self.get_data_fields(override=override),
                              label='Save',
                              href=request.url,
                              cancel=request.get_url('..')))


class ModifyPublicationFile(EditMixin, MethodMixin, RedirectMixin, POST):
    "Modify the list of files attached to the publication."

    fields = EditPublicationFile.fields

    def process(self, request):
        iui = self.publication['_id']
        datadir = os.path.join(configuration.DATA_DIR, iui)
        values = self.parse_fields(request)
        filenames = values.get('remove') or []
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
        pmid = values['pmid'].strip()
        if list(self.db.view('publication/excluded')[['pubmed', pmid]]):
            raise HTTP_CONFLICT('PubMed id has been excluded!')
        result = list(self.db.view('publication/xref')[['pubmed', pmid]])
        if result:
            iui = result[0].id
        else:
            article = pubmed.Article(pmid)
            if not article.pmid:
                raise HTTP_BAD_REQUEST("no article with PMID %s" % pmid)
            with PublicationSaver(self.db) as doc:
                doc.update(article.get_data())
                iui = doc['_id']
        self.set_redirect(request.application.get_url(iui))


class XrefPublication(MethodMixin, RedirectMixin, GET):
    "Look up the publication for the given xref, and redirect."

    def set_current(self, request):
        try:
            xdb, xkey = request.variables['xref'].split(':', 1)
        except ValueError:
            raise HTTP_BAD_REQUEST('invalid xref')
        view = self.db.view('publication/xref')
        result = list(view[[xdb.lower(), xkey]])
        if len(result) != 1:
            raise HTTP_NOT_FOUND
        self.set_redirect(request.application.get_url(result[0].id))


class PubmedPublication(MethodMixin, RedirectMixin, GET):
    "Look up the publication for the given PubMed ID, and redirect."

    def set_current(self, request):
        pmid = request.variables['pmid']
        view = self.db.view('publication/xref')
        result = list(view[['pubmed', pmid]])
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
