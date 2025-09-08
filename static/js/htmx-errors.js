// Displays a message when HTMX requests fail with a 403 status
(function () {
  document.body.addEventListener('htmx:responseError', function (evt) {
    if (evt.detail.xhr.status === 403) {
      alert('Session expired—please refresh.');
    }
  });
})();
