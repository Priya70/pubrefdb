""" PubRefDb: Publication database web application.

Update the database from PubMed; try to patch existing incomplete entries.

NOTE: This should really be done via the operation 'Update from PubMed'
in the web interface.
"""

import time

from pubrefdb import pubmed
from pubrefdb import configuration
from pubrefdb.database import PublicationSaver


def patch(db, delay=10.0, log=True):
    """Loop through all PubMed publications and attempt to patch up
    missing bits of information (type, published date, volume and pages).
    """
    for item in db.view('publication/xref')[['pubmed'] : ['pubmed', 'ZZZZZZ']]:
        doc = db[item.id]
        if publication_is_incomplete(db, doc):
            pmid = item.key[1]
            if log:
                print 'Checking', pmid
            patch_publication(db, pmid, log=log)
            time.sleep(delay)

def publication_is_incomplete(db, doc):
    assert doc['entitytype'] == 'publication'
    if not doc.get('type'): return True
    published = doc.get('published') or ''
    parts = published.split('-')
    if len(parts) < 3: return True
    if parts[1] == '00': return True
    # Do not bother about day in month.
    journal = doc.get('journal')
    if not journal: return True
    if not journal.get('volume'): return True
    # Do not bother about issue; is undefined for some journals.
    if not journal.get('pages'): return True
    return False

def patch_publication(db, pmid, log):
    article = pubmed.Article(pmid)
    if not article.pmid: return
    view = db.view('publication/xref', include_docs=True)
    results = list(view[['pubmed', pmid]])
    doc = results[0].doc
    if doc['type'] != article.type or \
       doc['published'] != article.published or \
       doc['journal'] != article.journal:
        with PublicationSaver(db, doc=doc):
            doc['type'] = article.type
            doc['published'] = article.published
            doc['journal'] = article.journal
            if log:
                print 'Updated', article.pmid, article.title
    return doc


if __name__ == '__main__':
    db = configuration.get_db()
    patch(db)
