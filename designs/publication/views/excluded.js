/* PubRefDb: Publication database web application.
   Index excluded publication documents by pubmed and doi xrefs (xdb + xkey).
   Value: id.
*/
function(doc) {
    if (doc.entitytype !== 'excluded') return;
    var xdb;
    for (var i in doc.xrefs) {
	xref = doc.xrefs[i];
	xdb = xref.xdb.toLowerCase();
	switch(xdb) {
	case 'pubmed':
	case 'doi': 
	    emit([xdb, xref.xkey], doc._id);
	    break;
	}
    }
}
