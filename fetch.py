""" PubRefDb: Publication database web application.

Fetch new publications from PubMed.

To be executed via cron script or the command line.

The result is recorded in the document 'fetched' in the database.
By default, loop over the current list of PIs for new publications and load.
If command-line arguments given, then check only those PIs.
"""

import time
import traceback

from wrapid.utils import now
from pubrefdb import pubmed
from pubrefdb import configuration
from pubrefdb.database import PublicationSaver


def fetch(db, pinames=[], years=[], delay=10.0):
    try:
        doc = db['fetched']
    except:
        doc = dict(_id='fetched',
                   entitytype='metadata')
    else:
        try:
            del doc['error']
        except KeyError:
            pass
    if not years:
        year = time.localtime().tm_year
        years = range(year-1, year+1)
    doc['pis'] = []
    doc['years'] = years
    try:
        first = True
        for pi, affiliations in get_pis_affiliations(db, explicit=pinames):
            record = dict(name=pi)
            if first:
                first = False
            else:
                time.sleep(delay)
            pmids = set()
            for year in years:
                search = pubmed.Search()
                for affiliation in affiliations:
                    pmids.update(search(author=pi,
                                        affiliation=affiliation,
                                        published=year))
            record['count'] = len(pmids)
            record['added'] = []
            for pmid in pmids:
                if add_publication(db, pmid):
                    record['added'].append(pmid)
            doc['pis'].append(record)
    except Exception, message:
        doc['error'] = traceback.format_exc(limit=20)
    doc['created'] = now()
    db.save(doc)

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
    fetch(configuration.get_db(), pinames=sys.argv[1:])
