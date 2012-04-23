/* PubRefDb: Publication database web application.
   Index publication documents by author.
   Value: id.
*/
function(doc) {
    if (doc.entitytype !== 'publication') return;
    var author, name;
    for (var i in doc.authors) {
	au = doc.authors[i];
	if (au.initials_normalized) {
	    name = au.lastname_normalized + ' ' + au.initials_normalized;
	} else {
	    name = au.lastname_normalized;
	}
	emit(name.toLowerCase(), doc._id);
    }
}
