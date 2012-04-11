/* PubListMan: Publication database web application.
   Index publication documents by author.
   Value: null. */
function(doc) {
    if (!doc.entitytype == 'publication') return;
    var author, name;
    for (var i in doc.authors) {
	au = doc.authors[i];
	if (au.lastname_normalized) {
	    name = au.lastname_normalized + ' ' + au.initials_normalized;
	} else {
	    name = au.forename_normalized;
	}
	emit(name.toLowerCase(), null);
    }
}
