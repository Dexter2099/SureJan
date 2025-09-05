// Handles certain HTMX error responses globally
(function () {
  function showToast(message) {
    var toast = document.createElement('div');
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.bottom = '1rem';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.background = '#333';
    toast.style.color = '#fff';
    toast.style.padding = '0.5rem 1rem';
    toast.style.borderRadius = '4px';
    toast.style.zIndex = '1000';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    document.body.appendChild(toast);
    requestAnimationFrame(function () { toast.style.opacity = '1'; });
    setTimeout(function () { toast.style.opacity = '0'; }, 2000);
    setTimeout(function () { toast.remove(); }, 2300);
  }

  function reenableVoteButtons(target) {
    if (!target) return;
    var container = target.closest('.vote, .comment-vote');
    if (!container) return;
    container.querySelectorAll('button').forEach(function (btn) {
      btn.disabled = false;
    });
  }

  document.body.addEventListener('htmx:beforeSwap', function (evt) {
    var status = evt.detail.xhr.status;
    if (status === 401) {
      var redirect = evt.detail.xhr.getResponseHeader('HX-Redirect');
      if (redirect) {
        window.location.href = redirect;
      }
      showToast('Please log in');
      reenableVoteButtons(evt.detail.target);
      evt.detail.shouldSwap = false;
    }
    if (status === 403) {
      showToast('Action forbidden');
      reenableVoteButtons(evt.detail.target);
      evt.detail.shouldSwap = false;
    }
    if (status === 409) {
      showToast("You've already voted");
      evt.detail.shouldSwap = false;
    }
    if (status >= 500 && status < 600) {
      evt.detail.shouldSwap = false;
    }
  });
}());
