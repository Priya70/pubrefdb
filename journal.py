""" PubRefDb: Publication database web application.

List of journals in the database.
"""

from .base import *
from .database import MetadataSaver


class JournalsHtmlRepresentation(HtmlRepresentation):

    def get_content(self):
        table = TABLE(TR(TH('Journal title'),
                         TH('# publications')),
                      klass='data')
        for journal in self.data['journals']:
            table.append(TR(TD(journal['title']),
                            TD(A(journal['count'],
                                 href=journal['href']),
                               klass='integer')))
        return table


class Journals(MethodMixin, GET):
    "Display list of journals in the database."

    outreprs = [JsonRepresentation,
                MedlineRepresentation,
                JournalsHtmlRepresentation]

    def get_data_resource(self, request):
        journals = []
        for item in self.db.view('publication/journals', group=True):
            journal = dict(title=item.key,
                           count=item.value,
                           href=request.application.get_url('search',
                                                            terms=item.key))
            journals.append(journal)
        return dict(title='Journals and number of publications',
                    journals=journals)
