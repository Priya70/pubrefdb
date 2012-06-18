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
    if parts[1] == '00': return True
    # Do not bother about day in month.
    journal = doc.get('journal')
    if not journal: return True
    if not journal.get('volume'): return True
    # Do not bother about issue; may not exist for some journals.
    if not journal.get('pages'): return True
    return False

def patch_publication(db, pmid):
    article = pubmed.Article(pmid)
    if not article.pmid: return
    view = db.view('publication/xref', include_docs=True)
    print pmid
    print view[pmid]
    results = list(view[pmid])
    print results
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
    import sys
    import time

    DELAY = 10
    db = configuration.get_db()

    for item in db.view('publication/xref')[['pubmed'] : ['pubmed', 'ZZZZZZ']]:
        doc = db[item.id]
        if is_incomplete(db, doc):
            print doc['title']
            patch_publication(db, item.key)
            time.sleep(DELAY)
