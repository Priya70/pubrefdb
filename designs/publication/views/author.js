/* PubRefDb: Publication database web application.
   Index publication documents by author.
   Value: null.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    var au, name;
    for (var i in doc.authors) {
	au = doc.authors[i];
	if (!au.lastname_normalized) continue;
	emit(au.lastname_normalized.toLowerCase(), null);
	if (au.initials_normalized) {
	    name = au.lastname_normalized + ' ' + au.initials_normalized;
	    emit(name.toLowerCase(), null);
	}
	if (au.forename_normalized) {
	    name = au.lastname_normalized + ' ' + au.forename_normalized;
	    emit(name.toLowerCase(), null);
	}
    }
}
