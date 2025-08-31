document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('textarea[data-editor]').forEach(setupEditor);
  const title = document.querySelector('#id_title');
  if (title) setupCounter(title);
});

document.body.addEventListener('htmx:afterSwap', (e) => {
  if (!e.detail || !e.detail.elt) return;
  e.detail.elt.querySelectorAll?.('textarea[data-editor]').forEach(setupEditor);
  const title = e.detail.elt.querySelector?.('#id_title');
  if (title) setupCounter(title);
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

