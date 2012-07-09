/* PubRefDb: Publication database web application.
   Index publication documents with PubMed xref which have incomplete data.
   Checks for defined values of :
   - Published date.
   - Published month.
   - Type of publication.
   - Journal.
   - Volume.
   - Pages.
   Published day and journal issue may be undefined.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    var pmid, xref;
    for (var i in doc.xrefs) {
	xref = doc.xrefs[i];
	if (xref.xdb.toLowerCase() === 'pubmed') {
	    pmid = xref.xkey;
	    break;
	}
    }
    if (!pmid) return;
    if (!doc.published) {
	emit(pmid, null);
	return;
    }
    var parts = doc.published.split('-');
    if (parts.length < 3 || parts[1] === '0' || parts[1] === '00' ) {
	emit(pmid, null);
	return;
    }
    if (!doc.type) {
	emit(pmid, null);
	return;
    }
    var journal = doc.journal;
    if (!journal) {
	emit(pmid, null);
	return;
    }
    if (!journal.volume) {
	emit(pmid, null);
	return;
    }
    if (!journal.pages) {
	emit(pmid, null);
	return;
    }
}
