// Handles certain HTMX error responses globally
(function () {
  document.body.addEventListener('htmx:beforeSwap', function (evt) {
    var status = evt.detail.xhr.status;
    if (status === 401) {
      var redirect = evt.detail.xhr.getResponseHeader('HX-Redirect');
      if (redirect) {
        window.location.href = redirect;
      }
      evt.detail.shouldSwap = false;
    }
    if (status === 403 || status === 409 || (status >= 500 && status < 600)) {
      evt.detail.shouldSwap = false;
    }
  });
}());
