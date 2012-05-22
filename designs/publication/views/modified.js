/* PubRefDb: Publication database web application.
   Index publication documents by modified date.
   Value: null.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    emit(doc.modified, null);
}
