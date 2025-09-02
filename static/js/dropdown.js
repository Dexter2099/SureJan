document.addEventListener('DOMContentLoaded', function () {
  var dropdown = document.querySelector('.communities-dropdown');
  if (!dropdown) return;
  var toggle = dropdown.querySelector('.communities-toggle');
  function closeMenu() {
    dropdown.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    var isOpen = dropdown.classList.toggle('open');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
  document.addEventListener('click', function (e) {
    if (!dropdown.contains(e.target)) {
      closeMenu();
    }
  });
});
