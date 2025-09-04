(function(){
  function validUrl(value){
    try {
      new URL(value);
      return true;
    } catch (e) {
      return false;
    }
  }

  function enableEmbeds(root){
    if (window.initEmbeds) {
      window.initEmbeds(root);
      return;
    }
    root.querySelectorAll('[data-embed-src]').forEach(function(wrapper){
      var link = wrapper.querySelector('a') || wrapper;
      var src = wrapper.dataset.embedSrc;
      if (!src || !link) return;
      link.addEventListener('click', function(e){
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
      }, { once: true });
    });
  }

  async function fetchPreview(url){
    const preview = document.getElementById('link-preview');
    if (!preview) return;
    if (!validUrl(url)){
      preview.innerHTML = '';
      return;
    }
    try {
      const resp = await fetch(`/oembed/preview/?url=${encodeURIComponent(url)}`);
      if (!resp.ok) {
        preview.innerHTML = '';
        return;
      }
      const html = await resp.text();
      preview.innerHTML = html;
      enableEmbeds(preview);
    } catch (e) {
      preview.innerHTML = '';
    }
  }

  document.addEventListener('DOMContentLoaded', function(){
    var input = document.getElementById('id_link');
    if (!input) return;
    input.addEventListener('input', function(e){
      fetchPreview(e.target.value.trim());
    });
  });
})();
