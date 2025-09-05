// Handles enabling/disabling the submit button on the post submit form.
document.addEventListener('DOMContentLoaded', () => {
  const titleEl = document.querySelector('#id_title');
  const bodyEl = document.querySelector('#id_body');
  const contentUrlEl = document.querySelector('#id_content_url');
  const imagesEl = document.querySelector('#id_images');
  const communityEl = document.querySelector('#id_community');
  const postTypeEls = document.querySelectorAll('input[name="post_type"]');

  function update() {
    const postType = document.querySelector('input[name="post_type"]:checked')?.value;
    const title = titleEl?.value.trim();
    const body = bodyEl?.value.trim();
    const contentUrl = contentUrlEl?.value.trim();
    const community = communityEl?.value;
    const imagesCount = imagesEl?.files?.length || 0;

    let ok = false;
    if (community && title) {
      if (postType === 'text') ok = !!body;
      else if (postType === 'link') ok = !!contentUrl;
      else if (postType === 'images') ok = imagesCount > 0;
    }

    const postBtn = document.querySelector('#post-btn');
    if (postBtn) postBtn.disabled = !ok;
  }

  [titleEl, bodyEl, contentUrlEl].forEach(el => {
    if (el) el.addEventListener('input', update);
  });
  if (communityEl) communityEl.addEventListener('change', update);
  if (imagesEl) imagesEl.addEventListener('change', update);
  postTypeEls.forEach(el => el.addEventListener('change', update));

  update();
});
