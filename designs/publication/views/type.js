/* PubRefDb: Publication database web application.
   Index publication documents by type.
   Value: null.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    if (!doc.type) return;
    emit(doc.type, null);
}
