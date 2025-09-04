// Adds Django CSRF header to all HTMX requests
(function () {
  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }
  document.body.addEventListener('htmx:configRequest', function (evt) {
    const token = csrfToken();
    if (token) {
      evt.detail.headers['X-CSRFToken'] = token;
    }
  });
}());
