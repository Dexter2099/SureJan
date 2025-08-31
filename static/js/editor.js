document.addEventListener('DOMContentLoaded', () => {
  const titleField = document.getElementById('id_title');
  const bodyField = document.getElementById('id_body');
  const urlField = document.getElementById('id_url');
  const postTypeField = document.getElementById('id_post_type');
  const titleCount = document.getElementById('title-count');
  const bodyCount = document.getElementById('body-count');
  const TITLE_MAX = 300;
  const BODY_MAX = 40000;

  function updateCount(field, counter, max) {
    if (!field || !counter) return;
    counter.textContent = `${field.value.length} / ${max}`;
  }

  if (titleField && titleCount) {
    updateCount(titleField, titleCount, TITLE_MAX);
    titleField.addEventListener('input', () => updateCount(titleField, titleCount, TITLE_MAX));
  }

  function autoResize(el) {
    if (!el) return;
    el.style.height = 'auto';
    const max = window.innerHeight * 0.6;
    const newHeight = Math.min(el.scrollHeight, max);
    el.style.height = newHeight + 'px';
  }

  if (bodyField && bodyCount) {
    updateCount(bodyField, bodyCount, BODY_MAX);
    autoResize(bodyField);
    bodyField.addEventListener('input', () => {
      updateCount(bodyField, bodyCount, BODY_MAX);
      autoResize(bodyField);
    });
  }

  const form = document.querySelector('.post-form');
  if (form) {
    form.addEventListener('submit', () => {
      if (postTypeField) {
        const urlVal = urlField && urlField.value.trim();
        postTypeField.value = urlVal ? 'link' : 'text';
      }
    });
  }
});
