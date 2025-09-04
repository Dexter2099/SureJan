// Handles previews for content URL and body fields on the post submit form.
document.addEventListener('DOMContentLoaded', () => {
  const urlInput = document.querySelector('#id_content_url');
  const bodyInput = document.querySelector('#id_body');
  const linkPreview = document.querySelector('#link-preview');
  const mdPreview = document.querySelector('#md-preview');
  const previewUrl = linkPreview?.dataset.previewUrl;
  const markdownUrl = mdPreview?.dataset.markdownUrl;

  let urlTimer;
  if (urlInput && linkPreview && previewUrl) {
    urlInput.addEventListener('input', () => {
      const value = urlInput.value.trim();
      clearTimeout(urlTimer);
      urlTimer = setTimeout(async () => {
        if (!value) {
          linkPreview.innerHTML = '';
          return;
        }
        try {
          const resp = await fetch(`${previewUrl}?url=${encodeURIComponent(value)}`);
          if (!resp.ok) {
            linkPreview.innerHTML = '';
            return;
          }
          const html = await resp.text();
          linkPreview.innerHTML = html;
          if (window.initEmbeds) window.initEmbeds(linkPreview);
        } catch (e) {
          linkPreview.innerHTML = '';
        }
      }, 350);
    });
  }

  let bodyTimer;
  if (bodyInput && mdPreview && markdownUrl) {
    bodyInput.addEventListener('input', () => {
      const value = bodyInput.value.trim();
      clearTimeout(bodyTimer);
      bodyTimer = setTimeout(async () => {
        if (!value) {
          mdPreview.innerHTML = '';
          return;
        }
        try {
          const params = new URLSearchParams({ body: value });
          const resp = await fetch(`${markdownUrl}?${params.toString()}`);
          if (!resp.ok) {
            mdPreview.innerHTML = '';
            return;
          }
          const html = await resp.text();
          mdPreview.innerHTML = html;
        } catch (e) {
          mdPreview.innerHTML = '';
        }
      }, 350);
    });
  }
});
