document.addEventListener('DOMContentLoaded', () => {
  document
    .querySelectorAll('textarea[data-editor]')
    .forEach(initEditor);
});

function initEditor(textarea) {
  const toolbar = textarea.previousElementSibling;
  if (!toolbar || !toolbar.classList.contains('editor-toolbar')) return;

  toolbar.querySelectorAll('button[data-action]').forEach((button) => {
    button.addEventListener('click', () => {
      applyAction(textarea, button.dataset.action);
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
      textarea.focus();
    });
  });
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

