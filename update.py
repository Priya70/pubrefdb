""" PubRefDb: Publication database web application.

Update the database from PubMed:
1) Load new publications, given the current list of PIs.
2) Try to patch existing incomplete entries.

If arguments given, then load new publications for those authors.
"""

import time

from pubrefdb import pubmed
from pubrefdb import configuration
from pubrefdb.database import PublicationSaver

def fetch(db, pinames=[], years=[], delay=10.0, log=True):
    if not years:
        year = time.localtime().tm_year
        years = range(year-1, year+1)
    pis = get_pis_affiliations(db, explicit=pinames)
    total = 0
    first = True
    for pi, affiliations in pis:
        if first:
            first = False
        else:
            time.sleep(delay)
        pmids = fetch_pmids(db, pi, years, affiliations)
        count_all = len(pmids)
        count_new = 0
        for pmid in pmids:
            if add_publication(db, pmid):
                count_new += 1
        if log:
            print pi, ':', count_all, 'found,', count_new, 'added'
        total += count_new
    return total

def get_pis_affiliations(db, explicit=[]):
    """Get the list of (PI name, affiliations).
    If any explicit names given (e.g. from command-line arguments),
    then pick only those from the db, else get all.
    """
    pis = db['pilist']['pis']
    names = set([n.lower().replace('_', ' ') for n in explicit])
    if names:
        for i, pi in enumerate(pis):
            name = pi.get('normalized_name', pi['name'])
            if name.lower() not in names:
                pis[i] = None
        pis = [pi for pi in pis if pi is not None]
    return [(pi.get('normalized_name', pi['name']),
             [a.strip() for a in pi['affiliation'].split(',')])
            for pi in pis]

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

def patch(db, delay=10.0, log=True):
    """Loop through all publications and attempt to patch up missing
    bits of information (type, published date, volume and pages).
    """
    for item in db.view('publication/xref')[['pubmed'] : ['pubmed', 'ZZZZZZ']]:
        doc = db[item.id]
        if publication_is_incomplete(db, doc):
            patch_publication(db, item.key, log=log)
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
    # Do not bother about issue; may not exist for some journals.
    if not journal.get('pages'): return True
    return False

def patch_publication(db, pmid, log):
    article = pubmed.Article(pmid)
    if not article.pmid: return
    view = db.view('publication/xref', include_docs=True)
    results = list(view[pmid])
    with PublicationSaver(db, doc=results[0].doc) as doc:
        doc['type'] = article.type
        doc['published'] = article.published
        doc['journal'] = article.journal
        if log:
            print 'Updated', article.pmid, article.title
    return doc


if __name__ == '__main__':
    import sys
    db = configuration.get_db()
    total = fetch(db, sys.argv[1:])
    print total, 'added in total'
    patch(db)
