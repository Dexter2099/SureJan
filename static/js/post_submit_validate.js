// Handles enabling/disabling the submit button on the post submit form.
document.addEventListener('DOMContentLoaded', () => {
  const titleEl = document.querySelector('#id_title');
  const bodyEl = document.querySelector('#id_body');
  const contentUrlEl = document.querySelector('#id_content_url');
  const imagesEl = document.querySelector('#id_images');
  const postTypeEls = document.querySelectorAll('input[name="post_type"]');

  function update() {
    const postType = document.querySelector('input[name="post_type"]:checked')?.value;
    const title = titleEl?.value.trim();
    const body = bodyEl?.value.trim();
    const contentUrl = contentUrlEl?.value.trim();
    const imagesHasValue = !!(
      imagesEl && ((imagesEl.files && imagesEl.files.length > 0) || imagesEl.value)
    );

    let ok = false;
    if (title) {
      if (postType === 'text') ok = !!body;
      else if (postType === 'link') ok = !!contentUrl;
      else if (postType === 'images') ok = imagesHasValue;
    }

    const postBtn = document.querySelector('#post-btn');
    if (postBtn) postBtn.disabled = !ok;
  }

  [titleEl, bodyEl, contentUrlEl, imagesEl].forEach(el => {
    if (el) el.addEventListener('input', update);
  });
  postTypeEls.forEach(el => el.addEventListener('change', update));

  update();
});
