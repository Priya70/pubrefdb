/* PubRefDb: Publication database web application.
   Index publication documents by PubMed ID (PMID).
   Value: null. */
function(doc) {
    if (doc.entitytype !== 'publication') return;
    for (var i in doc.xrefs) {
	xref = doc.xrefs[i];
	if (xref.xdb.toLowerCase() === 'pubmed') {
	    emit(xref.xkey, null);
	}
    }
}
