(function(){
  function collectImages(){
    const inputs = document.querySelectorAll('.image-url-input');
    const urls = Array.from(inputs).map(i => i.value.trim()).filter(Boolean);
    const hidden = document.getElementById('id_image_urls');
    if (hidden) hidden.value = urls.join('\n');
    return urls;
  }

  function validatePost(){
    const title = document.getElementById('id_title')?.value.trim();
    const body = document.getElementById('id_body')?.value.trim();
    const link = document.getElementById('id_link')?.value.trim();
    const images = collectImages();
    const buttons = document.querySelectorAll('#post-btn,#post-btn-mobile');
    const valid = title && (body || link || images.length);
    buttons.forEach(btn => { if(btn) btn.disabled = !valid; });
  }

  function updateType(){
    const type = document.querySelector('input[name="post_type"]:checked')?.value;
    const linkRow = document.getElementById('link-row');
    const imagesRow = document.getElementById('images-row');
    if (linkRow) linkRow.style.display = type === 'link' ? '' : 'none';
    if (imagesRow) imagesRow.style.display = type === 'images' ? '' : 'none';
    validatePost();
  }

  function updateLivePreview(){
    const liveToggle = document.getElementById('live-preview-toggle');
    const liveToggleMobile = document.getElementById('live-preview-toggle-mobile');
    const enabled = (liveToggle?.checked) || (liveToggleMobile?.checked);
    const previewUrl = document.getElementById('post-form')?.dataset.previewUrl;
    const fields = [document.getElementById('id_body')];
    fields.forEach(f => {
      if (!f) return;
      if (enabled){
        f.setAttribute('hx-post', previewUrl);
        f.setAttribute('hx-trigger', 'input delay:500ms');
        f.setAttribute('hx-target', '#preview');
        f.setAttribute('hx-swap', 'innerHTML');
      } else {
        f.removeAttribute('hx-post');
        f.removeAttribute('hx-trigger');
        f.removeAttribute('hx-target');
        f.removeAttribute('hx-swap');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('input', validatePost);
    document.querySelectorAll('input[name="post_type"]').forEach(r => r.addEventListener('change', updateType));
    document.getElementById('post-form')?.addEventListener('submit', collectImages);
    document.getElementById('live-preview-toggle')?.addEventListener('change', updateLivePreview);
    document.getElementById('live-preview-toggle-mobile')?.addEventListener('change', updateLivePreview);
    updateType();
    updateLivePreview();
  });
})();
