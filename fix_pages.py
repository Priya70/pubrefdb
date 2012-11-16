""" PubRefDb: Publication database web application.

Fix the pages entry to contain the complete page numbers for all publications.
"""

from pubrefdb import configuration


if __name__ == '__main__':
    db = configuration.get_db()
    for identifier in db:
        document = db[identifier]
        if document.get('entitytype') != 'publication': continue
        try:
            pages = document['journal']['pages']
        except KeyError:
            pass
        else:
            if pages:
                pages = pages.split('-')
                if len(pages) >= 2:
                    diff = len(pages[0]) - len(pages[1])
                    if diff > 0:
                        pages[1] = pages[0][0:diff] + pages[1]
                pages = '-'.join(pages)
            if pages != document['journal']['pages']:
                document['journal']['pages'] = pages
                print document['title'], document['journal']['pages']
                db.save(document)
