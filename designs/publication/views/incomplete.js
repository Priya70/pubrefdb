/* PubRefDb: Publication database web application.
   Index publication documents lacking information about:
   - Published date.
   - Published month.
   - Type of publication.
   - Journal.
   - Volume.
   - Pages.
   Published day and journal issue is not checked, and may be undefined.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    var pmid = null;
    for (var i in doc.xrefs) {
	var xref = doc.xrefs[i];
	if (xref.xdb.toLowerCase() === 'pubmed') {
	    pmid = xref.xkey;
	    break;
	}
    }
    if (!doc.published) {
	emit(doc._id, pmid);
	return;
    }
    var parts = doc.published.split('-');
    if (parts.length < 3 || parts[1] === '0' || parts[1] === '00' ) {
	emit(doc._id, pmid);
	return;
    }
    if (!doc.type) {
	emit(doc._id, pmid);
	return;
    }
    var journal = doc.journal;
    if (!journal) {
	emit(doc._id, pmid);
	return;
    }
    if (!journal.volume) {
	emit(doc._id, pmid);
	return;
    }
    if (!journal.pages) {
	emit(doc._id, pmid);
	return;
    }
}
