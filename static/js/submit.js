// Handles post type toggling and preview submission

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.post-form');
  if (!form) return;

  // Toggle post type modes
  const radios = form.querySelectorAll('input[name="post_type"]');
  const modes = {
    text: form.querySelector('.mode-text'),
    link: form.querySelector('.mode-link'),
    image: form.querySelector('.mode-image'),
  };
  function updateMode() {
    const val = form.querySelector('input[name="post_type"]:checked')?.value;
    Object.entries(modes).forEach(([key, el]) => {
      if (!el) return;
      const active = key === val;
      el.classList.toggle('active', active);
      el.hidden = !active;
    });
  }
  radios.forEach(r => r.addEventListener('change', updateMode));
  updateMode();

  // Preview button handler
  const previewBtn = document.getElementById('preview-btn');
  const previewPanel = document.getElementById('preview-panel');

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

  previewBtn?.addEventListener('click', () => {
    const fd = new FormData(form);
    fetch('/submit/preview/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: fd,
    })
      .then(res => res.text())
      .then(html => {
        if (previewPanel) previewPanel.innerHTML = html;
      });
  });
});
