""" PubRefDb: Publication database web application.

MEDLINE text representation class for publication and publications list.

XXX None for some values TA, PG: do not output
"""

from wrapid.text_representation import *


class MedlineRepresentation(TextRepresentation):

    def __call__(self, data):
        response = HTTP_OK(**self.get_http_headers())
        try:
            publications = data['publications']
        except KeyError:
            response.append(self.get_medline(data))
        else:
            result = [self.get_medline(p) for p in publications]
            response.append('\n\n'.join(result))
        return response

    def get_medline(self, publication):
        result = []
        for xref in publication.get('xrefs', []):
            if xref['xdb'] == 'pubmed':
                result.append("PMID- %s" % xref['xkey'])
                break
        try:
            result.append("TI  - %s" % self.multiline(publication['title']))
        except KeyError:
            pass
        try:
            result.append("AB  - %s" % self.multiline(publication['abstract']))
        except KeyError:
            pass
        try:
            result.append("AD  - %s" % self.multiline(publication['affiliation']))
        except KeyError:
            pass
        for author in publication.get('authors', []):
            try:
                result.append("AU  - %s %s" % (author['lastname_normalized'],
                                               author['initials_normalized']))
            except KeyError:
                pass
            # 'FAU': full name
        try:
            result.append("PT  - %s" % publication['type'])
        except KeyError:
            pass
        journal = publication.get('journal', dict())
        try:
            result.append("JT  - %s" % journal['title'])
        except KeyError:
            pass
        try:
            result.append("TA  - %s" % journal['abbreviation'])
        except KeyError:
            pass
        try:
            result.append("PG  - %s" % journal['pages'])
        except KeyError:
            pass
        try:
            result.append("IS  - %s" % journal['issn'])
        except KeyError:
            pass
        # XXX volume, issue, date of publication
        for xref in publication.get('xrefs', []):
            if xref['xdb'] == 'pubmed': continue
            result.append("AID - %s [%s]" % (xref['xkey'], xref['xdb']))
        return rstr('\n'.join(result))

    def multiline(self, text, maxlength=82):
        result = []
        line = []
        count = 0
        for word in text.split():
            increment = len(word) + 1
            if count + increment > maxlength:
                result.append(' '.join(line))
                line = []
                count = 0
            else:
                line.append(word)
                count += increment
        if line:
            result.append(' '.join(line))
        return '\n      '.join(result)
