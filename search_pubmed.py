""" PubRefDb: Publication database web application.

Search PubMed for new publications and load; loop through PIs in the database.
"""

import logging
import time

from pubrefdb import pubmed
from pubrefdb.database import get_db
from pubrefdb.method_mixin import add_article


def fetch_pi_pmids(db, pi, years, affiliations):
    """Get the PMIDs for publications involving the given PI
    at the given affiliations, for the specified years.
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
    view = db.view('publication/pmid')
    if len(view[pmid]) > 0: return
    article = pubmed.Article(pmid)
    if not article.pmid: return
    return add_article(db, article)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    year = time.localtime().tm_year
    years = range(year-2, year+1)
    db = get_db()
    pis = db['pilist']['pis']
    pis = [(pi['name'], [a.strip() for a in pi['affiliation'].split(',')])
           for pi in pis]
    for pi, affiliations in pis:
        pmids = fetch_pi_pmids(db, pi, years, affiliations)
        count_all = len(pmids)
        count_new = 0
        for pmid in pmids:
            if add_publication(db, pmid):
                count_new += 1
        logging.debug("%s: %i found, %i new", pi, count_all, count_new)
