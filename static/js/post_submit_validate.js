// Handles basic client-side validation for the post submit form.
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('#post-form');
  if (!form) return;

  const title = form.querySelector('#id_title');
  const body = form.querySelector('#id_body');
  const contentUrl = form.querySelector('#id_content_url');
  const image = form.querySelector('#id_image');
  const postBtn = document.querySelector('#post-btn');
  const postTypeRadios = form.querySelectorAll('input[name="post_type"]');

  const getType = () =>
    form.querySelector('input[name="post_type"]:checked')?.value;

  const validate = () => {
    const type = getType();
    const titleVal = title?.value.trim();
    const bodyVal = body?.value.trim();
    const urlVal = contentUrl?.value.trim();
    const filesLen = image?.files?.length || 0;

    let ok = false;
    if (type === 'text') {
      ok = !!(titleVal && bodyVal);
    } else if (type === 'link') {
      ok = !!(titleVal && urlVal);
    } else if (type === 'image') {
      ok = !!(titleVal && filesLen === 1);
    }

    if (postBtn) postBtn.disabled = !ok;
  };

  [title, body, contentUrl, image].forEach((el) => {
    el?.addEventListener('input', validate);
    el?.addEventListener('change', validate);
  });
  postTypeRadios.forEach((el) => el.addEventListener('change', validate));

  validate();
});

