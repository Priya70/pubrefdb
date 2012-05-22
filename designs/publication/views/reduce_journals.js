/* PubRefDb: Publication database web application.
   Reduce function to obtain all distinct journals (title abbrev) for count.
*/
function(keys, values, rereduce) {
    return sum(values);
}
