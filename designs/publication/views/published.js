/* PubRefDb: Publication database web application.
   Index publication documents by published date.
   Value: id.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    if (!doc.published) return;
    emit(doc.published, doc._id);
}
