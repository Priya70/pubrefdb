/* PubRefDb: Publication database web application.
   Index publication documents by xref (xdb + xkey).
   Value: id.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    for (var i in doc.xrefs) {
	xref = doc.xrefs[i];
	emit([xref.xdb.toLowerCase(), xref.xkey], doc._id);
    }
}
