/* PubRefDb: Publication database web application.
   Index publication documents by publication year for allowing count.
   Value: 1.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    if (!doc.published) return;
    var year = doc.published.split('-')[0];
    emit(year, 1);
}
