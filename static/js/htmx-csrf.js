// Adds Django CSRF header to all HTMX requests
(function () {
  function getCookie(name) {
    let v = null;
    if (document.cookie) {
      document.cookie.split(';').forEach(c => {
        c = c.trim();
        if (c.startsWith(name + '=')) v = decodeURIComponent(c.slice(name.length + 1));
      });
    }
    return v;
  }
  document.body.addEventListener('htmx:configRequest', function (evt) {
    evt.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
  });
}());
