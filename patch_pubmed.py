""" PubRefDb: Publication database web application.

Loop through all publications and attempt to patch up missing or changed
bits of info, such as type, published date, journal title.
"""

from pubrefdb import pubmed
from pubrefdb import configuration
from pubrefdb.database import PublicationSaver


def is_incomplete(db, doc):
    assert doc['entitytype'] == 'publication'
    if not doc.get('type'): return True
    published = doc.get('published') or ''
    parts = published.split('-')
    if len(parts) < 3: return True
    if parts[2] == '00': return True
    if parts[1] == '00': return True
    return False

def patch_publication(db, pmid):
    article = pubmed.Article(pmid)
    if not article.pmid: return
    view = db.view('publication/xref', include_docs=True)
    results = list(view[['pubmed', pmid]])
    with PublicationSaver(db, doc=results[0].doc) as doc:
        doc['type'] = article.type
        doc['published'] = article.published
        doc['journal'] = article.journal
        print 'saved', article.pmid
    return doc

def get_ids(db, indexname, key, last=None, **kwargs):
    """Get the list of document identifiers using the named index
    and the given key or interval.
    """
    view = db.view(indexname, **kwargs)
    if key is None:
        iterator = view
    elif last is None:
        iterator = view[key]
    else:
        iterator = view[key:last]
    return [i.value for i in iterator]
    

if __name__ == '__main__':
    import time
    DELAY = 10
    db = configuration.get_db()
    for item in db.view('publication/xref')[['pubmed'] : ['pubmed', 'ZZZZZZ']]:
        doc = db[item.value]
        if is_incomplete(db, doc):
            patch_publication(db, item.key)
            time.sleep(DELAY)
