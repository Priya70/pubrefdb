/* PubRefDb: Publication database web application.
   Reduce function to obtain all distinct tags, and count.
 */
function(key, values, rereduce) {
    return sum(values);
}
