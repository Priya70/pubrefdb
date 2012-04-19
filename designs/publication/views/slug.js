/* PubRefDb: Publication database web application.
   Index publication documents by slug.
   Value: id.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    if (!doc.slug) return;
    emit(doc.slug, doc._id);
}
