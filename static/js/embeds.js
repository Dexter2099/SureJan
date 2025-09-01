document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.post-embed[data-src]').forEach(function (wrapper) {
    var link = wrapper.querySelector('a');
    var src = wrapper.dataset.src;
    if (!link) return;
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var iframe = document.createElement('iframe');
      iframe.src = src;
      iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
      iframe.setAttribute('allowfullscreen', '');
      iframe.setAttribute('loading', 'lazy');
      iframe.style.position = 'absolute';
      iframe.style.top = '0';
      iframe.style.left = '0';
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      wrapper.innerHTML = '';
      wrapper.appendChild(iframe);
    });
  });
});
