(function(){
  function attach(wrapper, src, link){
    if (!src || !link) return;
    link.addEventListener('click', function(e){
      e.preventDefault();
      var iframe = document.createElement('iframe');
      iframe.src = src;
      iframe.setAttribute('allowfullscreen', '');
      iframe.setAttribute('loading', 'lazy');
      iframe.setAttribute('referrerpolicy', 'no-referrer');
      iframe.style.position = 'absolute';
      iframe.style.top = '0';
      iframe.style.left = '0';
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      wrapper.innerHTML = '';
      wrapper.appendChild(iframe);
    }, { once: true });
  }

  function initEmbeds(root){
    root = root || document;
    root.querySelectorAll('[data-src]').forEach(function(wrapper){
      attach(wrapper, wrapper.dataset.src, wrapper.querySelector('a'));
    });
  }

  window.initEmbeds = initEmbeds;
  document.addEventListener('DOMContentLoaded', function(){ initEmbeds(document); });
})();
