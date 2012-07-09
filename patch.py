""" PubRefDb: Publication database web application.

Update the database from PubMed; try to patch existing incomplete entries.

To be executed via cron, the command line or via the 'Update from PubMed'
operation in the web interface.
"""

import time

from pubrefdb import pubmed
from pubrefdb import configuration
from pubrefdb.database import PublicationSaver


def patch(db, delay=10.0, log=True):
    """Loop through all incomplete publications having PubMed xref
    and attempt to patch up missing bits of information:
    type of publication, published date and journal information.
    """
    view = db.view('publication/incomplete', include_docs=True)
    for item in view:
        pmid = item.key
        if log:
            print 'Checking', pmid
        article = pubmed.Article(pmid)
        if article.pmid:
            patch_publication(db, item.doc, article, log=log)
            time.sleep(delay)


def patch_publication(db, doc, article, log):
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
