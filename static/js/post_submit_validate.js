// Handles basic client-side validation for the post submit form.
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('#post-form');
  if (!form) return;

  const postType = form.querySelector('#id_post_type');
  const title = form.querySelector('#id_title');
  const body = form.querySelector('#id_body');
  const contentUrl = form.querySelector('#id_content_url');
  const images = form.querySelector('#id_images');
  const postBtn = document.querySelector('#post-btn');

  const validate = () => {
    const type = postType?.value;
    const titleVal = title?.value.trim();
    const bodyVal = body?.value.trim();
    const urlVal = contentUrl?.value.trim();
    const filesLen = images?.files?.length || 0;

    let ok = false;
    if (type === 'text') {
      ok = !!(titleVal && bodyVal);
    } else if (type === 'link') {
      ok = !!(titleVal && urlVal);
    } else if (type === 'images') {
      // Only require title and at least one image.
      ok = !!(titleVal && filesLen > 0);
    }

    if (postBtn) postBtn.disabled = !ok;
  };

  [postType, title, body, contentUrl, images].forEach((el) => {
    el?.addEventListener('input', validate);
    el?.addEventListener('change', validate);
  });

  validate();
});

