/* PubRefDb: Publication database web application.
   Index publication documents by modified date.
   Value: id.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    emit(doc.modified, doc._id);
}
