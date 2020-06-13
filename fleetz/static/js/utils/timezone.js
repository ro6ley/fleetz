/**
 * Handle rendering of time using the correct timezone.
 * It relies on Moment.js
 */
function handleTimezone(){
  $('.time').map(function() {
    this.innerHTML = moment(this.innerHTML).format("HH:mm, ddd DD MMM, YYYY");
    return this.innerHTML;
  });
}

$(document).ready(handleTimezone);
