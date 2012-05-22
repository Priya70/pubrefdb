/* PubRefDb: Publication database web application.
   Reduce function to obtain authors for count.
*/
function(keys, values, rereduce) {
    return sum(values);
}
