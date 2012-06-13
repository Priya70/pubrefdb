""" PubRefDb: Publication database web application.

Atom feed representation class.
"""

from wrapid.xml_representation import *

from . import configuration

ATOM_NAMESPACE = 'http://www.w3.org/2005/Atom'


class AtomRepresentation(XmlRepresentation):

    mimetype = 'application/atom+xml'
    format = 'atom'

    def data_to_element(self, data):
        "Return an ElementTree element produced from the data dictionary."
        self.builder = xml.etree.ElementTree.TreeBuilder()
        self.builder.start('feed', dict(xmlns=ATOM_NAMESPACE))
        self.simple_element('title', data['title'])
        self.link_element(data['href'], rel='self')
        self.link_element(data['application']['href'])
        for outrepr in data['outreprs']:
            self.link_element(outrepr['href'], type=outrepr['mimetype'])
        self.simple_element('id', data['href'])
        modified = '2010-01-01'
        for publication in data['publications']:
            modified = max(modified, publication['modified'])
        self.simple_element('updated', modified)
        for publication in data['publications']:
            self.builder.start('entry', {})
            self.simple_element('title', publication['title'])
            self.simple_element('id', publication['href'])
            self.link_element(publication['href'])
            self.simple_element('updated', publication['modified'])
            self.authors_element(publication['authors'])
            self.builder.end('entry')
        self.builder.end('feed')
        return self.builder.close()

    def simple_element(self, name, content):
        self.builder.start(name, {})
        self.builder.data(unicode(content))
        self.builder.end(name)

    def link_element(self, href, **kwargs):
        attrs = kwargs.copy()
        attrs['href'] = href
        self.builder.start('link', attrs)
        self.builder.end('link')

    def authors_element(self, authors):
        from .base import get_author_name
        for author in authors:
            self.builder.start('author', {})
            name = get_author_name(author)
            self.simple_element('name', name)
            self.builder.end('author')
