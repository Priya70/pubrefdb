""" PubRefDb: Publication database web application.

PubMed interface.
"""

import time
import urllib
import unicodedata
import xml.etree.ElementTree


MONTHS = dict(jan=1, feb=2, mar=3, apr=4, may=5, jun=6,
              jul=7, aug=8, sep=9, oct=10, nov=11, dec=12)

PUBMED_FETCH_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&rettype=abstract&id=%s'
PUBMED_SEARCH_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=%s&term=%s'


def to_ascii(value):
    "Convert any non-ASCII character to its closest equivalent."
    value = unicode(value)
    return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')


class Article(object):
    "Fetch and parse PubMed XML for a publication given by its PMID."

    def __init__(self, pmid=None):
        self.title = None
        self.authors = []
        self.affiliation = None
        self.journal = None
        self.type = None
        self.published = None
        self.abstract = None
        self.xrefs = []
        self.hrefs = []
        self.tags = []
        if pmid:
            root = self.fetch(pmid)
            self.parse(root.find('PubmedArticle'))

    def __str__(self):
        return "Article(%s)" % self.pmid

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
                    type=self.type,
                    published=self.published,
                    abstract= self.abstract,
                    xrefs=self.xrefs,
                    hrefs=self.hrefs,
                    tags=self.tags)

    def fetch(self, pmid):
        "Fetch the XML from PubMed and parse into an ElementTree."
        url = PUBMED_FETCH_URL % pmid
        infile = urllib.urlopen(url)
        code = infile.getcode() 
        if code < 200 or code >= 400:
            raise IOError("HTTP error %s" % code)
        data = infile.read()
        try:
            return xml.etree.ElementTree.fromstring(data)
        except:
            print data
            raise

    def parse(self, tree):
        "Parse the XML tree for the article information."
        if tree is None: return
        element = tree.find('MedlineCitation/Article')
        if not element:
            raise ValueError('invalid XML')
        self.title = element.findtext('ArticleTitle') or '[no title]'
        self.authors = self.get_authors(element.find('AuthorList'))
        self.affiliation = element.findtext('Affiliation') or None
        self.journal = self.get_journal(element)
        self.type = self.get_type(element)
        self.published = self.get_published(tree)
        self.abstract = self.get_abstract(element)
        self.xrefs = self.get_xrefs(tree)
        if self.pmid is None:
            pmid = tree.findtext('MedlineCitation/PMID')
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
                author[key + '_normalized'] = to_ascii(value)
            # For consortia and such, names are a mess. Try to sort out.
            if not author.get('lastname'):
                try:
                    author['lastname'] = author.pop('forename')
                except KeyError:
                    value = element.findtext('CollectiveName')
                    if not value: continue # Give up.
                    if not isinstance(value, unicode):
                        value = unicode(value, 'utf-8')
                    author['lastname'] = value
                author['forename'] = None
                author['initials'] = None
                author['lastname_normalized'] = to_ascii(author['lastname'])
                try:
                    author.pop('forename_normalized')
                except KeyError:
                    pass
                author['forename_normalized'] = None
                author['initials_normalized'] = None
            if author:
                result.append(author)
        return result

    def get_journal(self, article):
        result = dict()
        element = article.find('Journal')
        if element is not None:
            result['issn'] = element.findtext('ISSN')
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

    def get_type(self, article):
        element = article.find('PublicationTypeList/PublicationType')
        if element is not None:
            return element.text.lower()
        else:
            return None

    def get_published(self, article):
        elem = article.find('MedlineCitation/Article/Journal/JournalIssue/PubDate')
        date = []
        if elem is not None:
            date = self.get_date(elem)
        if len(date) < 2:               # Fallback 1: ArticleDate
            elem = article.find('MedlineCitation/Article/ArticleDate')
            if elem is not None:
                date = self.get_date(elem)
        if len(date) < 2:               # Fallback 2: PubMedPubDate
            dates = article.findall('PubmedData/History/PubMedPubDate')
            for status in ['epublish', 'aheadofprint', 'pubmed']:
                for elem in dates:
                    if elem.get('PubStatus') == status:
                        date = self.get_date(elem)
                        break
                if len(date) >= 2: break
        if len(date) == 0:              # Fallback 3: today's year and month
            d = time.localtime()
            date = [d.tm_year, d.tm_mon, 0]
        elif len(date) == 1:            # Add today's month
            d = time.localtime()
            date = [date[0], d.tm_mon, 0]
        elif len(date) == 2:            # Add dummy day
            date.append(0)
        return "%s-%02i-%02i" % tuple(date)

    def get_abstract(self, element):
        sections = []
        for elem in element.findall('Abstract/AbstractText'):
            sections.append(elem.text)
        return '\n\n'.join(sections)

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


class Search(object):
    "Simple search interface, producing a list of PMIDs."

    def __init__(self, retmax=100):
        self.retmax = retmax

    def __call__(self, author=None, published=None, journal=None,
                 affiliation=None, words=None):
        parts = []
        if author:
            parts.append("%s[Author]" % to_ascii(author))
        if published:
            parts.append("%s[PDAT]" % published)
        if journal:
            parts.append("%s[Journal]" % journal)
        if affiliation:
            parts.append("%s[Affiliation]" % to_ascii(affiliation))
        if words:
            parts.append(words.replace(' ', '+'))
        url = PUBMED_SEARCH_URL % (self.retmax, ' AND '.join(parts))
        data = urllib.urlopen(url).read()
        root = xml.etree.ElementTree.fromstring(data)
        return [e.text for e in root.findall('IdList/Id')]


def test1():
    search = Search()
    pmids = search(author='Kere J',
                   words='dyslexia')
                   ## published='2012',
                   ## affiliation='Karolinska Institute')
    for pmid in pmids:
        print pmid
    print 'Total:', len(pmids)

def test2():
    search('(("2010"[PData - Publication] : "3000"[Date - Publication])) AND kere j[Author]')
    search('(2010[PDAT] AND kere j[Author]')
    search('"2010"[Date - Publication] AND kere j[Author]')


if __name__ == '__main__':
    url = PUBMED_FETCH_URL % '21572409'
    infile = urllib.urlopen(url)
    data = infile.read()
    open('data/colwill_2011.xml', 'w').write(data)
    ## import json
    ## root = xml.etree.ElementTree.fromstring(open('data/borgstrom_2011.xml').read())
    ## article = Article()
    ## article.parse(root.find('PubmedArticle'))
    ## ## article=Article(pmid='11751858')
    ## print json.dumps(article.get_data(), indent=2)
