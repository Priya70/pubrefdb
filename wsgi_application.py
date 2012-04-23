""" PubRefDb: Publication database web application.

Apache WSGI interface using the 'wrapid' package.
"""

import wrapid
assert wrapid.__version__ == '12.4'
from wrapid.application import Application
from wrapid.login import Login
from wrapid.file import File

import pubrefdb
from pubrefdb import configuration
from pubrefdb.home import *
from pubrefdb.publication import *
from pubrefdb.year import *
from pubrefdb.author import *
from pubrefdb.journal import *
from pubrefdb.tag import *
from pubrefdb.pilist import *
from pubrefdb.search import *
from pubrefdb.about import *
from pubrefdb.documentation import *


application = Application(name='PubRefDb',
                          version=pubrefdb.__version__,
                          host=configuration.HOST,
                          debug=configuration.DEBUG)


# Home: most recent publications
application.add_resource('/',
                         name='Home',
                         GET=Home)

# Static resources; accessed often, keep at beginning of the chain.
class StaticFile(File):
    "Return the specified file from a predefined server directory."
    dirpath = configuration.STATIC_DIR

application.add_resource('/static/{filepath:path}',
                         name='File',
                         GET=StaticFile)

application.add_resource('/{iui:uuid}',
                         name='Publication',
                         GET=Publication,
                         DELETE=DeletePublication)
application.add_resource('/{iui:uuid}/edit',
                         name='Publication edit',
                         GET=EditPublication,
                         POST=ModifyPublication)
application.add_resource('/{iui:uuid}/xrefs',
                         name='Publication xrefs',
                         GET=EditPublicationXrefs,
                         POST=ModifyPublicationXrefs)
application.add_resource('/{iui:uuid}/hrefs',
                         name='Publication hrefs',
                         GET=EditPublicationHrefs,
                         POST=ModifyPublicationHrefs)
application.add_resource('/{iui:uuid}/tags',
                         name='Publication tags',
                         GET=EditPublicationTags,
                         POST=ModifyPublicationTags)
application.add_resource('/{iui:uuid}/slug',
                         name='Publication slug',
                         GET=EditPublicationSlug,
                         POST=ModifyPublicationSlug)
application.add_resource('/{iui:uuid}/file',
                         name='Publication edit file',
                         GET=EditPublicationFile,
                         POST=ModifyPublicationFile)
application.add_resource('/{iui:uuid}/file/{filepath:path}',
                         name='Publication file',
                         GET=PublicationFile)
application.add_resource('/pubmed',
                         name='Publication import',
                         GET=InputPubmedPublication,
                         POST=ImportPubmedPublication)
application.add_resource('/pubmed/{pmid:integer}',
                         name='Publication lookup pmid',
                         GET=PubmedPublication)

# Lists of publication
application.add_resource('/year/{year:integer}',
                         name='Publication list year',
                         GET=Year)
application.add_resource('/author/{author}',
                         name='Publication list author',
                         GET=Author)
application.add_resource('/journals',
                         name='Journal list',
                         GET=Journals)
application.add_resource('/tag/{tag}',
                         name='Publication list tag',
                         GET=Tag)

# Other resources
application.add_resource('/search',
                         name='Publication search',
                         GET=Search)

# Edit PI list
application.add_resource('/pilist',
                         name='PI list',
                         GET=EditPiList,
                         POST=ModifyPiList)

# Login and account resources
class LoginAccount(Login):
    "Perform login to an account. Basic Authentication."
    def get_account(self, name, password):
        return configuration.users.get_account(name, password)

application.add_resource('/login', name='Login',
                         GET=LoginAccount)

# Documentation resources
application.add_resource('/about',
                         name='Documentation About',
                         GET=About)
application.add_resource('/doc',
                         name='Documentation API',
                         GET=ApiDocumentation)

# Slug-based publication lookup and redirect; must be last in this chain
application.add_resource('/{slug:path}',
                         name='Publication lookup slug',
                         GET=SlugPublication)
