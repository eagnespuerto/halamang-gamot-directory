// Light/dark toggle in the footer. The choice is saved in this browser; without one the page follows the system.
(function () {
  var button = document.getElementById('theme-toggle');
  if (!button) return;
  var root = document.documentElement;
  button.hidden = false;
  button.addEventListener('click', function () {
    var dark = root.dataset.theme
      ? root.dataset.theme === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches;
    var next = dark ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
  });
})();
