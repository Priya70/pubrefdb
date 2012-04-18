/* PubRefDb: Publication database web application.
   Index publication documents by journal title (abbreviated).
   Value: null.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    if (!doc.journal) return;
    emit(doc.journal.abbreviation || doc.journal.title, null);
}
