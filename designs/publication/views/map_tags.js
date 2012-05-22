/* PubRefDb: Publication database web application.
   Index publication documents by tag for count.
   Value: 1.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    if (!doc.tags) return;
    for (var i in doc.tags) {
	emit(doc.tags[i], 1);
    }
}
