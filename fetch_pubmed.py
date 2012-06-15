""" PubRefDb: Publication database web application.

Search and load publications from PubMed; loop through PIs in the database.
"""

from pubrefdb import pubmed
from pubrefdb import configuration
from pubrefdb.database import PublicationSaver

def fetch_pmids(db, pi, years, affiliations):
    """Get the PMIDs for publications involving the given PI
    at the given affiliations for the specified years.
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
    """Add the publication to the database if not already in it.
    Skip if the PMID has been excluded.
    Set the tag 'SciLifeLab' if marked such in the affiliation.
    """
    if len(db.view('publication/xref')[['pubmed', pmid]]) > 0: return
    if len(db.view('publication/excluded')[['pubmed', pmid]]) > 0: return
    article = pubmed.Article(pmid)
    if not article.pmid: return
    affiliation = article.affiliation or ''
    affiliation = affiliation.lower()
    for key in ['science for life laboratory', 'scilifelab']:
        if key in affiliation:
            article.tags.append('SciLifeLab')
            break
    with PublicationSaver(db, doc=article.get_data()) as doc:
        pass
    return doc


if __name__ == '__main__':
    import sys
    import time

    DELAY = 10

    year = time.localtime().tm_year
    ## years = range(2010, year+1)
    years = range(year-1, year+1)
    db = configuration.get_db()
    pis = db['pilist']['pis']
    # If any names given on command line, then check only those
    names = set([a.lower().replace('_', ' ') for a in sys.argv[1:]])
    if names:
        for i, pi in enumerate(pis):
            name = pi.get('normalized_name', pi['name'])
            if name.lower() not in names:
                pis[i] = None
        pis = [pi for pi in pis if pi is not None]
    pis = [(pi.get('normalized_name', pi['name']),
            [a.strip() for a in pi['affiliation'].split(',')])
           for pi in pis]
    total = 0
    first = True
    for pi, affiliations in pis:
        if first:
            first = False
        else:
            time.sleep(DELAY)
        pmids = fetch_pmids(db, pi, years, affiliations)
        count_all = len(pmids)
        count_new = 0
        for pmid in pmids:
            if add_publication(db, pmid):
                count_new += 1
        print pi, ':', count_all, 'found,', count_new, 'added'
        total += count_new
    print total, 'added in total'
