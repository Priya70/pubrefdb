""" PubRefDb: Publication database web application.

PubMed interface.
"""

import time
import urllib
import xml.etree.ElementTree

from pubrefdb import configuration

## url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=science%5bjournal%5d+AND+breast+cancer+AND+2008%5bpdat%5d"

MONTHS = dict(jan=1, feb=2, mar=3, apr=4, may=5, jun=6,
              jul=7, aug=8, sep=9, oct=10, nov=11, dec=12)


class Article(object):

    def __init__(self, pmid=None):
        self.title = None
        self.authors = []
        self.affiliation = None
        self.journal = None
        self.published = None
        self.abstract = None
        self.xrefs = []
        self.hrefs = []
        if pmid:
            root = self.fetch(pmid)
            self.parse(root.find('PubmedArticle'))

    @property
    def pmid(self):
        for xref in self.xrefs:
            if xref['xdb'].lower() == 'pubmed':
                return xref['xkey']
        else:
            return None

    def get_data(self):
        return dict(title=self.title,
                    authors=self.authors,
                    affiliation=self.affiliation,
                    journal=self.journal,
                    published=self.published,
                    abstract= self.abstract,
                    xrefs=self.xrefs,
                    hrefs=self.hrefs)

    def fetch(self, pmid):
        "Fetch the XML from PubMed and parse into an ElementTree."
        url = configuration.PUBMED_XML_URL % pmid
        infile = urllib.urlopen(url)
        data = infile.read()
        print 'type of data', type(data)
        data = unicode(data)
        print 'type of data', type(data)
        return xml.etree.ElementTree.fromstring(data)

    def parse(self, article):
        "Parse the XML tree for the article information."
        if article is None: return
        element = article.find('MedlineCitation/Article')
        if not element:
            raise ValueError('invalid XML')
        self.title = element.findtext('ArticleTitle') or '[no title]'
        self.authors = self.get_authors(element.find('AuthorList'))
        self.affiliation = element.findtext('Affiliation') or None
        self.journal = self.get_journal(element)
        self.abstract = self.get_abstract(element)
        self.published = self.get_published(article)
        self.xrefs = self.get_xrefs(article)
        if self.pmid is None:
            pmid = article.findtext('MedlineCitation/PMID')
            self.xrefs.append(dict(xdb='pubmed', xkey=pmid))

    def get_authors(self, authorlist):
        result = []
        for element in authorlist.findall('Author'):
            author = dict()
            for key in ['LastName', 'ForeName', 'Initials']:
                value = element.findtext(key)
                if not value: continue
                if not isinstance(value, unicode):
                    value = unicode(value, 'utf-8')
                key = key.lower()
                author[key] = value
                author[key + '_normalized'] = configuration.to_ascii(value)
            if author:
                result.append(author)
        return result

    def get_journal(self, article):
        result = dict()
        element = article.find('Journal')
        if element is not None:
            result['title'] = element.findtext('Title')
            result['abbreviation'] = element.findtext('ISOAbbreviation')
            issue = element.find('JournalIssue')
            if issue is not None:
                result['volume'] = issue.findtext('Volume')
                result['issue'] = issue=issue.findtext('Issue')
        element = article.find('Pagination/MedlinePgn')
        if element is not None:
            result['pages'] = element.text
        return result

    def get_xrefs(self, article):
        result = []
        for elem in article.findall('PubmedData/ArticleIdList/ArticleId'):
            result.append(dict(xdb=elem.get('IdType'), xkey=elem.text))
        for elem in article.findall('MedlineCitation/Article/DataBankList/DataBank'):
            xdb = elem.findtext('DataBankName')
            if not xdb: continue
            for elem2 in elem.findall('AccessionNumberList/AccessionNumber'):
                result.append(dict(xdb=xdb, xkey=elem2.text))
        return result
        
    def get_abstract(self, element):
        sections = []
        for elem in element.findall('Abstract/AbstractText'):
            sections.append(elem.text)
        return '\n\n'.join(sections)

    def get_published(self, article):
        elem = article.find('MedlineCitation/Article/Journal/JournalIssue/PubDate')
        date = []
        if elem:
            date = self.get_date(elem)
        if len(date) < 3:               # Fallback 1: epublish date
            for elem in article.findall('PubmedData/History/PubMedPubDate'):
                if elem.get('PubStatus') == 'epublish':
                    date = self.get_date(elem)
                    break
        if len(date) < 3:               # Fallback 2: today's date
            date = time.localtime()
            date = [date.tm_year, date.tm_mon, date.tm_mday]
        return "%s-%02i-%02i" % tuple(date)

    def get_date(self, element):
        "Return [year, month, day]"
        year = element.findtext('Year')
        if not year:
            return []
        result = [int(year)]
        month = element.findtext('Month')
        if not month:
            return result
        try:
            month = int(MONTHS.get(month.lower()[:3], month))
        except (TypeError, ValueError):
            return result
        else:
            result.append(month)
        day = element.findtext('Day')
        try:
            day = int(day)
        except (TypeError, ValueError):
            day = 0
        result.append(day)
        return result


if __name__ == '__main__':
    import json

    url = configuration.PUBMED_XML_URL % '22375924'
    infile = urllib.urlopen(url)
    data = infile.read()
    open('rosin_2012.xml', 'w').write(data)
    ## root = xml.etree.ElementTree.fromstring(open('borgstrom_2011.xml').read())
    ## root = xml.etree.ElementTree.fromstring(open('johansson_2002.xml').read())
    ## article = Article()
    ## article.parse(root.find('PubmedArticle'))
    ## article=Article(pmid='11751858')
    ## print json.dumps(article.get_data(), indent=2)
