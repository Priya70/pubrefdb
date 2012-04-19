/* PubRefDb: Publication database web application.
   Index publication documents by tag.
   Value: id.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    if (!doc.tags) return;
    for (var i in doc.tags) {
	emit(doc.tags[i], doc._id);
    }
}
