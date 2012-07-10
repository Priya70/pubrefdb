/* PubRefDb: Publication database web application.
   Index publication documents by title words, ignoring common short words.
   Value: null.
*/

/* Must be kept in sync with search.py */
var RSTRIP = /[-\.:,?]$/;
var IGNORE = {
    'a': 1,
    'an': 1,
    'and': 1,
    'are': 1,
    'as': 1,
    'at': 1,
    'but': 1,
    'by': 1,
    'can': 1,
    'for': 1,
    'from': 1,
    'into': 1,
    'in': 1,
    'is': 1,
    'of': 1,
    'on': 1,
    'or': 1,
    'that': 1,
    'the': 1,
    'to': 1,
    'using': 1,
    'with': 1
};

function(doc) {
    if (doc.entitytype !== 'publication') return;
    var words = doc.title.split(/\s+/);
    var word;
    for (var i in words) {
	word = words[i].toLowerCase();
	word = word.replace(RSTRIP, '');
	if (IGNORE[word]) continue;
	emit(word, null);
    }
}