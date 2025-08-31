document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('textarea[data-editor]').forEach(setupEditor);
  document.querySelectorAll('.post-form, .comment-form').forEach(setupDraft);
  const title = document.querySelector('#id_title');
  if (title) setupCounter(title);
  const contentUrl = document.querySelector('#id_content_url');
  if (contentUrl) setupDomainHint(contentUrl);
});

document.body.addEventListener('htmx:afterSwap', (e) => {
  if (!e.detail || !e.detail.elt) return;
  e.detail.elt.querySelectorAll?.('textarea[data-editor]').forEach(setupEditor);
  e.detail.elt.querySelectorAll?.('.post-form, .comment-form').forEach(setupDraft);
  const title = e.detail.elt.querySelector?.('#id_title');
  if (title) setupCounter(title);
  const contentUrl = e.detail.elt.querySelector?.('#id_content_url');
  if (contentUrl) setupDomainHint(contentUrl);
});

function setupEditor(textarea) {
  if (textarea.dataset.editorReady) return;
  textarea.dataset.editorReady = '1';

  const toolbar = textarea.previousElementSibling;
  if (toolbar && toolbar.classList.contains('editor-toolbar')) {
    toolbar.querySelectorAll('button[data-action]').forEach((button) => {
      button.addEventListener('click', () => {
        applyAction(textarea, button.dataset.action);
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.focus();
      });
    });
  }

  textarea.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      textarea.form?.requestSubmit();
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
      e.preventDefault();
      applyAction(textarea, 'bold');
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'i') {
      e.preventDefault();
      applyAction(textarea, 'italic');
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });

  const resize = () => {
    const max = window.innerHeight * 0.6;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, max) + 'px';
  };
  textarea.addEventListener('input', resize);
  window.addEventListener('resize', resize);
  resize();

  setupCounter(textarea);

  // Handle Write/Preview tab switching
  const container = textarea.closest('.editor-container');
  const writeTab = container?.querySelector('.tab-write');
  const previewTab = container?.querySelector('.tab-preview');
  const preview = container?.querySelector('.preview');
  const showWrite = () => {
    writeTab?.classList.add('active');
    previewTab?.classList.remove('active');
    textarea.style.display = '';
    if (toolbar) toolbar.style.display = '';
    if (preview) preview.style.display = 'none';
  };
  const showPreview = () => {
    previewTab?.classList.add('active');
    writeTab?.classList.remove('active');
    textarea.style.display = 'none';
    if (toolbar) toolbar.style.display = 'none';
    if (preview) preview.style.display = '';
  };
  writeTab?.addEventListener('click', (e) => {
    e.preventDefault();
    showWrite();
  });
  previewTab?.addEventListener('click', () => {
    showPreview();
  });
}

function setupCounter(field) {
  if (field.dataset.counterReady) return;
  field.dataset.counterReady = '1';

  const max = parseInt(
    field.getAttribute('maxlength') || field.dataset.max || (field.tagName === 'TEXTAREA' ? '10000' : '300'),
    10,
  );
  let counter = field.parentElement.querySelector('.char-count');
  if (!counter) {
    counter = document.createElement('div');
    counter.className = 'char-count';
    field.insertAdjacentElement('afterend', counter);
  }
  const update = () => {
    const len = field.value.length;
    counter.textContent = `${len}/${max}`;
    counter.classList.toggle('near-limit', len > max * 0.9 && len <= max);
    counter.classList.toggle('over-limit', len > max);
  };
  field.addEventListener('input', update);
  update();
}

function setupDomainHint(field) {
  if (field.dataset.domainReady) return;
  field.dataset.domainReady = '1';

  let hint = field.parentElement.querySelector('.domain-hint');
  if (!hint) {
    hint = document.createElement('div');
    hint.className = 'domain-hint';
    hint.style.display = 'none';
    field.insertAdjacentElement('afterend', hint);
  }
  const update = () => {
    try {
      const url = new URL(field.value);
      hint.textContent = url.hostname;
      hint.style.display = '';
    } catch {
      hint.textContent = '';
      hint.style.display = 'none';
    }
  };
  field.addEventListener('input', update);
  update();
}

function setupDraft(form) {
  if (form.dataset.draftReady) return;
  form.dataset.draftReady = '1';

  const key = getDraftKey(form);
  if (!key) return;

  const pill = form.querySelector('.draft-pill');
  const save = () => {
    const data = {};
    form.querySelectorAll('input, textarea').forEach((el) => {
      if (el.name) data[el.name] = el.value;
    });
    try {
      localStorage.setItem(key, JSON.stringify(data));
    } catch {}
  };
  const restore = () => {
    try {
      const data = JSON.parse(localStorage.getItem(key) || '{}');
      Object.entries(data).forEach(([name, value]) => {
        const field = form.querySelector(`[name="${name}"]`);
        if (field) field.value = value;
      });
      form.querySelectorAll('input, textarea').forEach((el) => {
        el.dispatchEvent(new Event('input', { bubbles: true }));
      });
    } catch {}
    pill.hidden = true;
  };
  const discard = () => {
    localStorage.removeItem(key);
    pill.hidden = true;
  };

  const existing = localStorage.getItem(key);
  if (existing && pill) {
    pill.hidden = false;
    pill.innerHTML =
      '<button type="button" class="restore-draft">Restore</button> / <button type="button" class="discard-draft">Discard</button>';
    pill.querySelector('.restore-draft')?.addEventListener('click', restore);
    pill.querySelector('.discard-draft')?.addEventListener('click', discard);
  }

  form.addEventListener('input', save);
  const interval = setInterval(save, 5000);
  const cleanup = () => {
    clearInterval(interval);
    localStorage.removeItem(key);
  };

  form.addEventListener('submit', (e) => {
    if (form.classList.contains('post-form')) {
      const body = form.querySelector('textarea[name="body"]');
      const urlField = form.querySelector('input[name="content_url"]');
      if (body && urlField && !urlField.value.trim()) {
        const text = body.value.trim();
        if (isOnlyUrl(text)) {
          if (confirm('Move URL to URL field?')) {
            urlField.value = text;
            urlField.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }
      }
    }
    cleanup();
  });
  window.addEventListener('beforeunload', save);
}

function getDraftKey(form) {
  if (form.classList.contains('post-form')) {
    const match = form.action.match(/\/c\/([^/]+)/);
    const slug = match ? match[1] : 'global';
    return `postDraft:${slug}`;
  }
  if (form.classList.contains('comment-form')) {
    const post = form.querySelector('input[name="post"]')?.value;
    if (post) return `commentDraft:${post}`;
  }
  return null;
}

function isOnlyUrl(text) {
  return /^https?:\/\/\S+$/.test(text);
}

function applyAction(textarea, action) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = textarea.value.slice(start, end);

  let replacement = selected;
  switch (action) {
    case 'bold':
      replacement = `**${selected}**`;
      break;
    case 'italic':
      replacement = `*${selected}*`;
      break;
    case 'link': {
      const url = prompt('URL');
      if (!url) return;
      replacement = `[${selected || 'text'}](${url})`;
      break;
    }
    case 'code':
      replacement = `\`${selected}\``;
      break;
    case 'bullets':
      replacement = selected
        .split('\n')
        .map((line) => `- ${line}`)
        .join('\n');
      break;
    case 'numbers':
      replacement = selected
        .split('\n')
        .map((line, i) => `${i + 1}. ${line}`)
        .join('\n');
      break;
    default:
      return;
  }

  textarea.setRangeText(replacement, start, end, 'end');
}

window.setupEditor = setupEditor;

