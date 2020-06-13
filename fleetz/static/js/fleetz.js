import './utils/confirm.js';
import './utils/timezone.js';

class Fleetz {
  /**
   * Main setup for Fleetz application.
   */
  setup() {
    // setup CSRF
    this.csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // inject CSRF token into Ajax requests
    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
        const requiresToken = !(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type));
        if (requiresToken && !this.crossDomain) {
          xhr.setRequestHeader("X-CSRFToken", this.csrfToken);
        }
      }
    });
  }
}

let fleetz = new Fleetz();
export default fleetz;
