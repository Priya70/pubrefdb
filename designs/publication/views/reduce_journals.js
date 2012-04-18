/* PubRefDb: Publication database web application.
   Reduce function to obtain all distinct journals (title abbrev), and count.
*/
function(key, values, rereduce) {
    return sum(values);
}
