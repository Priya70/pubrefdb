""" PubRefDb: Publication database web application.

MEDLINE text representation class for publication and publications list.

XXX DP: Date of publication (with month 3-letter silliness)
XXX FAU: full author name
"""

from wrapid.text_representation import *

MONTH = {1: 'Jan',
         2: 'Feb',
         3: 'Mar',
         4: 'Apr',
         5: 'May',
         6: 'Jun',
         7: 'Jul',
         8: 'Aug',
         9: 'Sep',
         10: 'Oct',
         11: 'Nov',
         12: 'Dec'}


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
                self.line(result, 'PMID', xref['xkey'])
                break
        try:
            self.multiline(result, 'TI', publication['title'])
        except KeyError:
            pass
        try:
            self.multiline(result, 'AB', publication['abstract'])
        except KeyError:
            pass
        try:
            self.multiline(result, 'AD', publication['affiliation'])
        except KeyError:
            pass
        for author in publication.get('authors', []):
            try:
                name = "%s %s" % (author['lastname_normalized'],
                                  author['initials_normalized'])
                self.multiline(result, 'AU', name)
            except KeyError:
                pass
        try:
            self.line(result, 'PT', publication['type'])
        except KeyError:
            pass
        journal = publication.get('journal', dict())
        try:
            self.line(result, 'JT', journal['title'])
        except KeyError:
            pass
        try:
            self.line(result, 'TA', journal['abbreviation'])
        except KeyError:
            pass
        try:
            self.line(result, 'VI', journal['volume'])
        except KeyError:
            pass
        try:
            self.line(result, 'IP', journal['issue'])
        except KeyError:
            pass
        try:
            self.line(result, 'PG', journal['pages'])
        except KeyError:
            pass
        try:
            self.line(result, 'IS', journal['issn'])
        except KeyError:
            pass
        try:
            published = publication['published']
            parts = published.split('-')
            if not parts: raise KeyError
        except KeyError:
            pass
        else:
            published = parts[0]
            try:
                published += ' ' + MONTH[int(parts[1])]
            except (IndexError, ValueError, KeyError):
                pass
            else:
                try:
                    published += ' ' + parts[2]
                except IndexError:
                    pass
            self.line(result, 'DP', published)
        for xref in publication.get('xrefs', []):
            if xref['xdb'] == 'pubmed': continue
            self.line(result, 'AID', "%s [%s]" % (xref['xkey'], xref['xdb']))
        return rstr('\n'.join(result))

    def line(self, result, symbol, value):
        if not value: return
        result.append("%-4s- %s" % (symbol, value))

    def multiline(self, result, symbol, value, maxlength=82):
        lines = []
        line = []
        count = 0
        for word in value.split():
            increment = len(word) + 1
            if count + increment > maxlength:
                lines.append(' '.join(line))
                line = []
                count = 0
            else:
                line.append(word)
                count += increment
        if line:
            lines.append(' '.join(line))
        self.line(result, symbol, '\n      '.join(lines))
