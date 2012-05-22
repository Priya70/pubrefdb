/* PubRefDb: Publication database web application.
   Reduce function to obtain years of publication for count.
*/
function(keys, values, rereduce) {
    return sum(values);
}
