/* PubListMan: Publication database web application.
   Index publication documents by published datetime.
   Value: null. */
function(doc) {
    if (!doc.entitytype == 'publication') return;
    if (!doc.published) return;
    emit(doc.published, null);
}
