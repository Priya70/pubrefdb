""" PubRefDb: Publication database web application.

Apache WSGI interface using the 'wrapid' package.
"""

import wrapid
assert wrapid.__version__ == '12.4'
from wrapid.application import Application
from wrapid.login import GET_Login
from wrapid.file import GET_File

import pubrefdb
from pubrefdb import configuration
from pubrefdb.home import *
from pubrefdb.publication import *
from pubrefdb.year import *
from pubrefdb.author import *
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
                         GET=GET_Home)

# Static resources; accessed often, keep at beginning of the chain.
class StaticFile(GET_File):
    "Return the specified file from a predefined server directory."
    dirpath = configuration.STATIC_DIR

application.add_resource('/static/{filename:path}',
                         name='File',
                         GET=StaticFile)

application.add_resource('/{iui:uuid}',
                         name='Publication',
                         GET=Publication)
## application.add_resource('/{iui:uuid}/edit',
##                          name='Publication edit',
##                          GET=GET_PublicationEdit,
##                          POST=POST_PublicationEdit)
application.add_resource('/pubmed',
                         name='Publication import',
                         GET=InputPublicationPubmed,
                         POST=ImportPublicationPubmed)

# Lists of publication
application.add_resource('/year/{year:integer}',
                         name='Publication list year',
                         GET=Year)
application.add_resource('/author/{author}',
                         name='Publication list author',
                         GET=Author)

# Other resources
application.add_resource('/search',
                         name='Publication search',
                         GET=Search)

# Edit PI list
application.add_resource('/pilist',
                         GET=DisplayPiList,
                         POST=ModifyPiList)

# Login and account resources
class LoginAccount(GET_Login):
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
