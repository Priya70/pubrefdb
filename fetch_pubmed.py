""" PubRefDb: Publication database web application.

Search and load publications from PubMed; loop through PIs in the database.
"""

from pubrefdb import pubmed
from pubrefdb.database import get_db
from pubrefdb.method_mixin import PublicationSaver


def fetch_pmids(db, pi, years, affiliations):
    """Get the PMIDs for publications involving the given PI
    at the given affiliations for the specified years.
    Remove thos PMIDs which already exist in the database.
    """
    pmids = set()
    for year in years:
        search = pubmed.Search()
        for affiliation in affiliations:
            pmids.update(search(author=pi,
                                affiliation=affiliation,
                                published=year))
    return sorted(pmids)

def add_publication(db, pmid):
    "Add the publication to the database if not already in it."
    view = db.view('publication/pmid')
    if len(view[pmid]) > 0: return
    article = pubmed.Article(pmid)
    if not article.pmid: return
    with PublicationSaver(db, doc=article.get_data()) as doc:
        pass
    return doc


if __name__ == '__main__':
    import sys
    import time
    year = time.localtime().tm_year
    years = range(year-2, year+1)
    db = get_db()
    pis = db['pilist']['pis']
    # If any names given on command line, then check only those
    names = set([a.lower().replace('_', ' ') for a in sys.argv[1:]])
    if names:
        for i, pi in enumerate(pis):
            if pi['name'].lower() not in names:
                pis[i] = None
        pis = [pi for pi in pis if pi is not None]
    pis = [(pi['name'], [a.strip() for a in pi['affiliation'].split(',')])
           for pi in pis]
    for pi, affiliations in pis:
        pmids = fetch_pmids(db, pi, years, affiliations)
        count_all = len(pmids)
        count_new = 0
        for pmid in pmids:
            if add_publication(db, pmid):
                count_new += 1
        print pi, ':', count_all, 'found,', count_new, 'added'
